"""
BackendGeneratorService: Generates and deploys NestJS backends from BlueprintV3.

This service:
1. Converts Blueprint to Prisma schema
2. Generates NestJS backend code
3. Builds and deploys as Docker container
4. Manages container lifecycle
"""

import os
import json
import logging
import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

from app.config import settings
from app.schemas.blueprint import BlueprintV3
from app.services.amplication_converter import AmplicationConverter

logger = logging.getLogger(__name__)

# Base path for generated apps
GENERATED_APPS_PATH = os.getenv("GENERATED_APPS_PATH", "/var/lib/blueprint-apps")

# Port range for generated backends
PORT_RANGE_START = 4001
PORT_RANGE_END = 4999

# Docker network name for app containers
DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "refine-supabase-apps-builder_default")

# Database connection for generated apps
DB_HOST = os.getenv("DB_HOST", "appsbuilder-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "appsbuilder")


class BackendGeneratorService:
    """Generates and manages NestJS backends from BlueprintV3."""

    def __init__(self):
        self.converter = AmplicationConverter()
        self.apps_path = Path(GENERATED_APPS_PATH)
        self.apps_path.mkdir(parents=True, exist_ok=True)
        self._docker_client = None
        self._used_ports: set = set()
        
    @property
    def docker_client(self):
        """Lazy initialization of Docker client."""
        if self._docker_client is None:
            if not DOCKER_AVAILABLE:
                raise RuntimeError("Docker SDK not available. Install with: pip install docker")
            try:
                self._docker_client = docker.from_env()
                # Test connection
                self._docker_client.ping()
                logger.info("Docker client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise RuntimeError(f"Cannot connect to Docker: {e}")
        return self._docker_client
    
    def _get_used_ports(self) -> set:
        """Get set of ports currently used by app containers."""
        used = set()
        try:
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if container.name.startswith("blueprint-app-"):
                    ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
                    for port_binding in ports.values():
                        if port_binding:
                            for binding in port_binding:
                                used.add(int(binding.get("HostPort", 0)))
        except Exception as e:
            logger.warning(f"Failed to get used ports: {e}")
        return used

    async def generate_backend(
        self, 
        app_id: UUID, 
        blueprint: BlueprintV3,
        db_schema: str
    ) -> Dict[str, Any]:
        """
        Generate a complete NestJS backend from BlueprintV3.
        
        Returns:
            Dict with backend_url, port, container_id, status
        """
        app_dir = self.apps_path / str(app_id)
        
        try:
            # 1. Create app directory
            app_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. Generate Prisma schema
            prisma_schema = self.converter.generate_prisma_schema(blueprint)
            
            # 3. Generate NestJS project structure
            await self._generate_nestjs_project(app_dir, blueprint, prisma_schema, db_schema)
            
            # 4. Allocate port
            port = await self._allocate_port(app_id)
            
            # 5. Generate metadata
            metadata = {
                "app_id": str(app_id),
                "app_name": blueprint.app.name,
                "app_slug": blueprint.app.slug,
                "port": port,
                "db_schema": db_schema,
                "status": "generated",
                "entities": [t.name for t in blueprint.data.tables],
            }
            
            # Save metadata
            with open(app_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Generated backend for app {app_id} at {app_dir}")
            
            # 6. Deploy the backend (build and run Docker container)
            try:
                deploy_result = await self.deploy_backend(app_id)
                return {
                    "backend_url": deploy_result.get("backend_url", f"http://localhost:{port}/api"),
                    "port": deploy_result.get("port", port),
                    "status": deploy_result.get("status", "running"),
                    "path": str(app_dir),
                    "container_id": deploy_result.get("container_id"),
                    "container_name": deploy_result.get("container_name"),
                }
            except Exception as deploy_error:
                logger.error(f"Failed to deploy backend for app {app_id}: {deploy_error}")
                # Return generated status - deployment can be retried
                return {
                    "backend_url": f"http://localhost:{port}/api",
                    "port": port,
                    "status": "generated",
                    "path": str(app_dir),
                    "deploy_error": str(deploy_error),
                }
            
        except Exception as e:
            logger.error(f"Failed to generate backend for app {app_id}: {e}")
            raise

    async def _generate_nestjs_project(
        self, 
        app_dir: Path, 
        blueprint: BlueprintV3,
        prisma_schema: str,
        db_schema: str
    ):
        """Generate NestJS project structure."""
        
        # Create directories
        src_dir = app_dir / "src"
        prisma_dir = app_dir / "prisma"
        src_dir.mkdir(exist_ok=True)
        prisma_dir.mkdir(exist_ok=True)
        
        # Write Prisma schema
        with open(prisma_dir / "schema.prisma", "w") as f:
            f.write(prisma_schema)
        
        # Generate package.json
        package_json = self._generate_package_json(blueprint)
        with open(app_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Generate main.ts
        main_ts = self._generate_main_ts()
        with open(src_dir / "main.ts", "w") as f:
            f.write(main_ts)
        
        # Generate app.module.ts
        app_module = self._generate_app_module(blueprint)
        with open(src_dir / "app.module.ts", "w") as f:
            f.write(app_module)
        
        # Generate Prisma service
        prisma_service = self._generate_prisma_service()
        with open(src_dir / "prisma.service.ts", "w") as f:
            f.write(prisma_service)
        
        # Generate entity modules
        for table in blueprint.data.tables:
            await self._generate_entity_module(src_dir, table, blueprint)
        
        # Generate Dockerfile
        dockerfile = self._generate_dockerfile()
        with open(app_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        # Generate .env
        env_content = self._generate_env(db_schema)
        with open(app_dir / ".env", "w") as f:
            f.write(env_content)
        
        # Generate tsconfig.json
        tsconfig = self._generate_tsconfig()
        with open(app_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)

    def _generate_package_json(self, blueprint: BlueprintV3) -> Dict[str, Any]:
        """Generate package.json for NestJS project."""
        return {
            "name": f"backend-{blueprint.app.slug}",
            "version": "1.0.0",
            "description": blueprint.app.description or f"Backend for {blueprint.app.name}",
            "scripts": {
                "build": "nest build",
                "start": "nest start",
                "start:dev": "nest start --watch",
                "start:prod": "node dist/main",
                "prisma:generate": "prisma generate",
                "prisma:migrate": "prisma migrate deploy",
                "prisma:push": "prisma db push"
            },
            "dependencies": {
                "@nestjs/common": "^10.0.0",
                "@nestjs/core": "^10.0.0",
                "@nestjs/platform-express": "^10.0.0",
                "@nestjs/swagger": "^7.0.0",
                "@prisma/client": "^5.0.0",
                "class-transformer": "^0.5.1",
                "class-validator": "^0.14.0",
                "reflect-metadata": "^0.1.13",
                "rxjs": "^7.8.1"
            },
            "devDependencies": {
                "@nestjs/cli": "^10.0.0",
                "@types/node": "^20.0.0",
                "prisma": "^5.0.0",
                "typescript": "^5.0.0"
            }
        }

    def _generate_main_ts(self) -> str:
        """Generate main.ts entry point."""
        return '''import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // Enable CORS
  app.enableCors({
    origin: '*',
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
  });
  
  // Global validation pipe
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    transform: true,
  }));
  
  // Swagger setup
  const config = new DocumentBuilder()
    .setTitle('Generated API')
    .setDescription('Auto-generated REST API')
    .setVersion('1.0')
    .addBearerAuth()
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);
  
  // Set global prefix
  app.setGlobalPrefix('api');
  
  const port = process.env.PORT || 3000;
  await app.listen(port);
  console.log(`Application is running on: http://localhost:${port}/api`);
}
bootstrap();
'''

    def _generate_app_module(self, blueprint: BlueprintV3) -> str:
        """Generate app.module.ts with all entity modules."""
        imports = ["import { Module } from '@nestjs/common';"]
        imports.append("import { PrismaService } from './prisma.service';")
        
        module_imports = []
        for table in blueprint.data.tables:
            module_name = f"{table.name}Module"
            imports.append(f"import {{ {module_name} }} from './{table.name.lower()}/{table.name.lower()}.module';")
            module_imports.append(module_name)
        
        return f'''{chr(10).join(imports)}

@Module({{
  imports: [{', '.join(module_imports)}],
  providers: [PrismaService],
  exports: [PrismaService],
}})
export class AppModule {{}}
'''

    def _generate_prisma_service(self) -> str:
        """Generate Prisma service."""
        return '''import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
'''

    async def _generate_entity_module(
        self, 
        src_dir: Path, 
        table, 
        blueprint: BlueprintV3
    ):
        """Generate module, controller, service for an entity."""
        entity_name = table.name
        entity_lower = entity_name.lower()
        entity_dir = src_dir / entity_lower
        entity_dir.mkdir(exist_ok=True)
        dto_dir = entity_dir / "dto"
        dto_dir.mkdir(exist_ok=True)
        
        # Generate module
        module_content = self._generate_entity_module_file(entity_name)
        with open(entity_dir / f"{entity_lower}.module.ts", "w") as f:
            f.write(module_content)
        
        # Generate controller
        controller_content = self._generate_controller(entity_name, table)
        with open(entity_dir / f"{entity_lower}.controller.ts", "w") as f:
            f.write(controller_content)
        
        # Generate service
        service_content = self._generate_service(entity_name, table)
        with open(entity_dir / f"{entity_lower}.service.ts", "w") as f:
            f.write(service_content)
        
        # Generate DTOs
        create_dto = self._generate_create_dto(entity_name, table, blueprint)
        with open(dto_dir / f"create-{entity_lower}.dto.ts", "w") as f:
            f.write(create_dto)
        
        update_dto = self._generate_update_dto(entity_name, table)
        with open(dto_dir / f"update-{entity_lower}.dto.ts", "w") as f:
            f.write(update_dto)

    def _generate_entity_module_file(self, entity_name: str) -> str:
        """Generate entity module file."""
        entity_lower = entity_name.lower()
        return f'''import {{ Module }} from '@nestjs/common';
import {{ {entity_name}Controller }} from './{entity_lower}.controller';
import {{ {entity_name}Service }} from './{entity_lower}.service';
import {{ PrismaService }} from '../prisma.service';

@Module({{
  controllers: [{entity_name}Controller],
  providers: [{entity_name}Service, PrismaService],
  exports: [{entity_name}Service],
}})
export class {entity_name}Module {{}}
'''

    def _generate_controller(self, entity_name: str, table) -> str:
        """Generate REST controller for entity."""
        entity_lower = entity_name.lower()
        return f'''import {{ Controller, Get, Post, Put, Delete, Body, Param, Query }} from '@nestjs/common';
import {{ ApiTags, ApiOperation, ApiQuery }} from '@nestjs/swagger';
import {{ {entity_name}Service }} from './{entity_lower}.service';
import {{ Create{entity_name}Dto }} from './dto/create-{entity_lower}.dto';
import {{ Update{entity_name}Dto }} from './dto/update-{entity_lower}.dto';

@ApiTags('{entity_lower}')
@Controller('{entity_lower}')
export class {entity_name}Controller {{
  constructor(private readonly {entity_lower}Service: {entity_name}Service) {{}}

  @Get()
  @ApiOperation({{ summary: 'Get all {entity_lower}s' }})
  @ApiQuery({{ name: '_start', required: false, type: Number }})
  @ApiQuery({{ name: '_end', required: false, type: Number }})
  @ApiQuery({{ name: '_sort', required: false, type: String }})
  @ApiQuery({{ name: '_order', required: false, enum: ['ASC', 'DESC'] }})
  async findAll(
    @Query('_start') start?: number,
    @Query('_end') end?: number,
    @Query('_sort') sort?: string,
    @Query('_order') order?: 'ASC' | 'DESC',
  ) {{
    return this.{entity_lower}Service.findAll({{ start, end, sort, order }});
  }}

  @Get(':id')
  @ApiOperation({{ summary: 'Get {entity_lower} by id' }})
  async findOne(@Param('id') id: string) {{
    return this.{entity_lower}Service.findOne(id);
  }}

  @Post()
  @ApiOperation({{ summary: 'Create {entity_lower}' }})
  async create(@Body() createDto: Create{entity_name}Dto) {{
    return this.{entity_lower}Service.create(createDto);
  }}

  @Put(':id')
  @ApiOperation({{ summary: 'Update {entity_lower}' }})
  async update(@Param('id') id: string, @Body() updateDto: Update{entity_name}Dto) {{
    return this.{entity_lower}Service.update(id, updateDto);
  }}

  @Delete(':id')
  @ApiOperation({{ summary: 'Delete {entity_lower}' }})
  async remove(@Param('id') id: string) {{
    return this.{entity_lower}Service.remove(id);
  }}
}}
'''

    def _generate_service(self, entity_name: str, table) -> str:
        """Generate service for entity."""
        entity_lower = entity_name.lower()
        return f'''import {{ Injectable, NotFoundException }} from '@nestjs/common';
import {{ PrismaService }} from '../prisma.service';
import {{ Create{entity_name}Dto }} from './dto/create-{entity_lower}.dto';
import {{ Update{entity_name}Dto }} from './dto/update-{entity_lower}.dto';

interface FindAllOptions {{
  start?: number;
  end?: number;
  sort?: string;
  order?: 'ASC' | 'DESC';
}}

@Injectable()
export class {entity_name}Service {{
  constructor(private prisma: PrismaService) {{}}

  async findAll(options: FindAllOptions = {{}}) {{
    const start = options.start !== undefined && !isNaN(Number(options.start)) ? Number(options.start) : 0;
    const end = options.end !== undefined && !isNaN(Number(options.end)) ? Number(options.end) : 10;
    const sort = options.sort || 'createdAt';
    const order = options.order || 'DESC';
    
    const take = end - start;
    const skip = start;
    
    const [data, total] = await Promise.all([
      this.prisma.{entity_lower}.findMany({{
        skip: skip > 0 ? skip : undefined,
        take: take > 0 ? take : 10,
        orderBy: {{ [sort]: order.toLowerCase() }},
      }}),
      this.prisma.{entity_lower}.count(),
    ]);
    
    return {{ data, total }};
  }}

  async findOne(id: string) {{
    const item = await this.prisma.{entity_lower}.findUnique({{
      where: {{ id }},
    }});
    
    if (!item) {{
      throw new NotFoundException(`{entity_name} with ID ${{id}} not found`);
    }}
    
    return item;
  }}

  async create(createDto: Create{entity_name}Dto) {{
    return this.prisma.{entity_lower}.create({{
      data: createDto,
    }});
  }}

  async update(id: string, updateDto: Update{entity_name}Dto) {{
    try {{
      return await this.prisma.{entity_lower}.update({{
        where: {{ id }},
        data: updateDto,
      }});
    }} catch (error) {{
      throw new NotFoundException(`{entity_name} with ID ${{id}} not found`);
    }}
  }}

  async remove(id: string) {{
    try {{
      return await this.prisma.{entity_lower}.delete({{
        where: {{ id }},
      }});
    }} catch (error) {{
      throw new NotFoundException(`{entity_name} with ID ${{id}} not found`);
    }}
  }}
}}
'''

    def _generate_create_dto(self, entity_name: str, table, blueprint: BlueprintV3 = None) -> str:
        """Generate Create DTO."""
        fields = []
        imports = ["import { ApiProperty } from '@nestjs/swagger';"]
        
        # Get relation names to filter out (we'll use FK columns instead)
        relation_names = set()
        if blueprint and blueprint.data.relationships:
            for rel in blueprint.data.relationships:
                if rel.fromTable == table.name and rel.type == "many_to_one":
                    relation_names.add(rel.name)  # e.g., "project"
        
        validators = set()
        validators.add("IsOptional")  # Always need IsOptional for optional fields
        
        for col in table.columns:
            # Skip columns that are relation names (use FK column instead)
            if col.name in relation_names:
                # Add the FK column instead
                fk_name = f"{col.name}Id"
                validators.add("IsString")
                fields.append(f'''
  @ApiProperty({{ required: false, description: 'FK to {col.name}' }})
  @IsOptional()
  @IsString()
  {fk_name}?: string;''')
                continue
            
            decorator = self._get_validator_decorator(col)
            validator_decorator = ""
            if decorator:
                validators.add(decorator[0])
                validator_decorator = f"\n  {decorator[1]}"
            
            optional_decorator = "" if col.required else "\n  @IsOptional()"
            optional = "" if col.required else "?"
            ts_type = self._to_typescript_type(col.type)
            
            fields.append(f'''
  @ApiProperty({{ required: {str(col.required).lower()} }}){optional_decorator}{validator_decorator}
  {col.name}{optional}: {ts_type};''')
        
        imports.append(f"import {{ {', '.join(sorted(validators))} }} from 'class-validator';")
        
        return f'''{chr(10).join(imports)}

export class Create{entity_name}Dto {{{chr(10).join(fields)}
}}
'''

    def _generate_update_dto(self, entity_name: str, table) -> str:
        """Generate Update DTO (all fields optional)."""
        entity_lower = entity_name.lower()
        return f'''import {{ PartialType }} from '@nestjs/swagger';
import {{ Create{entity_name}Dto }} from './create-{entity_lower}.dto';

export class Update{entity_name}Dto extends PartialType(Create{entity_name}Dto) {{}}
'''

    def _get_validator_decorator(self, col) -> Optional[Tuple[str, str]]:
        """Get class-validator decorator for column type."""
        type_validators = {
            "text": ("IsString", "@IsString()"),
            "int": ("IsInt", "@IsInt()"),
            "float": ("IsNumber", "@IsNumber()"),
            "bool": ("IsBoolean", "@IsBoolean()"),
            "date": ("IsDateString", "@IsDateString()"),
            "timestamptz": ("IsDateString", "@IsDateString()"),
        }
        return type_validators.get(col.type)

    def _to_typescript_type(self, blueprint_type: str) -> str:
        """Convert Blueprint type to TypeScript type."""
        type_map = {
            "uuid": "string",
            "text": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "date": "string",
            "timestamptz": "string",
            "jsonb": "any",
        }
        return type_map.get(blueprint_type, "string")

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for NestJS app."""
        return '''FROM node:20-slim

WORKDIR /app

# Install OpenSSL for Prisma
RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm install

# Generate Prisma client
RUN npx prisma generate

# Copy source code
COPY . .

# Build
RUN npm run build

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "run", "start:prod"]
'''

    def _generate_env(self, db_schema: str) -> str:
        """Generate .env file."""
        # Use the main database with schema
        db_url = f"postgresql://postgres:postgres@db:5432/appsbuilder?schema={db_schema}"
        return f'''DATABASE_URL="{db_url}"
PORT=3000
'''

    def _generate_tsconfig(self) -> Dict[str, Any]:
        """Generate tsconfig.json."""
        return {
            "compilerOptions": {
                "module": "commonjs",
                "declaration": True,
                "removeComments": True,
                "emitDecoratorMetadata": True,
                "experimentalDecorators": True,
                "allowSyntheticDefaultImports": True,
                "target": "ES2021",
                "sourceMap": True,
                "outDir": "./dist",
                "baseUrl": "./",
                "incremental": True,
                "skipLibCheck": True,
                "strictNullChecks": False,
                "noImplicitAny": False,
                "strictBindCallApply": False,
                "forceConsistentCasingInFileNames": False,
                "noFallthroughCasesInSwitch": False
            }
        }

    async def _allocate_port(self, app_id: UUID) -> int:
        """Allocate an available port for the app."""
        used_ports = self._get_used_ports()
        used_ports.update(self._used_ports)
        
        # Try to find an available port
        for port in range(PORT_RANGE_START, PORT_RANGE_END):
            if port not in used_ports:
                self._used_ports.add(port)
                return port
        
        # Fallback: use hash-based allocation
        hash_val = hash(str(app_id))
        port = PORT_RANGE_START + (abs(hash_val) % (PORT_RANGE_END - PORT_RANGE_START))
        return port

    async def deploy_backend(self, app_id: UUID) -> Dict[str, Any]:
        """
        Build and deploy the generated backend as a Docker container.
        
        Steps:
        1. Build Docker image from generated code
        2. Create and run container with allocated port
        3. Run Prisma migrations
        4. Update metadata with container_id and status
        """
        app_dir = self.apps_path / str(app_id)
        metadata_file = app_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"App {app_id} not found")
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        port = metadata.get("port", await self._allocate_port(app_id))
        container_name = f"blueprint-app-{str(app_id)[:12]}"
        image_name = f"blueprint-app-{str(app_id)[:12]}:latest"
        
        try:
            # 1. Stop and remove existing container if any
            await self._stop_container(container_name)
            
            # 2. Build Docker image
            logger.info(f"Building Docker image for app {app_id}...")
            metadata["status"] = "building"
            self._save_metadata(metadata_file, metadata)
            
            image, build_logs = await self._build_image(app_dir, image_name)
            logger.info(f"Built image {image_name} for app {app_id}")
            
            # 3. Create and start container
            logger.info(f"Starting container {container_name} on port {port}...")
            metadata["status"] = "starting"
            self._save_metadata(metadata_file, metadata)
            
            container = await self._run_container(
                image_name=image_name,
                container_name=container_name,
                port=port,
                db_schema=metadata.get("db_schema", f"app_{str(app_id).replace('-', '')[:12]}")
            )
            
            # 4. Wait for container to be healthy
            logger.info(f"Waiting for container {container_name} to be ready...")
            await self._wait_for_container(container, timeout=120)
            
            # 5. Run Prisma migrations
            logger.info(f"Running Prisma migrations for app {app_id}...")
            metadata["status"] = "migrating"
            self._save_metadata(metadata_file, metadata)
            
            await self._run_prisma_push(container)
            
            # 6. Update metadata
            metadata["status"] = "running"
            metadata["container_id"] = container.id
            metadata["container_name"] = container_name
            metadata["image_name"] = image_name
            metadata["backend_url"] = f"http://localhost:{port}/api"
            metadata["port"] = port
            self._save_metadata(metadata_file, metadata)
            
            logger.info(f"Successfully deployed backend for app {app_id} at port {port}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to deploy backend for app {app_id}: {e}")
            metadata["status"] = "error"
            metadata["error"] = str(e)
            self._save_metadata(metadata_file, metadata)
            raise
    
    def _save_metadata(self, metadata_file: Path, metadata: Dict[str, Any]):
        """Save metadata to file."""
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _stop_container_sync(self, container_name: str):
        """Stop and remove a container if it exists (synchronous)."""
        try:
            container = self.docker_client.containers.get(container_name)
            logger.info(f"Stopping existing container {container_name}...")
            container.stop(timeout=10)
            container.remove(force=True)
            logger.info(f"Removed container {container_name}")
        except docker.errors.NotFound:
            pass  # Container doesn't exist, that's fine
        except Exception as e:
            logger.warning(f"Error stopping container {container_name}: {e}")

    async def _stop_container(self, container_name: str):
        """Stop and remove a container if it exists (async wrapper)."""
        await asyncio.to_thread(self._stop_container_sync, container_name)
    
    def _build_image_sync(self, app_dir: Path, image_name: str) -> Tuple[Any, List[str]]:
        """Build Docker image from app directory (synchronous)."""
        logs = []
        
        try:
            # Build image using Docker SDK
            image, build_logs = self.docker_client.images.build(
                path=str(app_dir),
                tag=image_name,
                rm=True,
                forcerm=True,
                nocache=False,
            )
            
            # Collect logs
            for chunk in build_logs:
                if 'stream' in chunk:
                    log_line = chunk['stream'].strip()
                    if log_line:
                        logs.append(log_line)
                        logger.debug(f"Build: {log_line}")
                elif 'error' in chunk:
                    error_msg = chunk['error']
                    logger.error(f"Build error: {error_msg}")
                    raise RuntimeError(f"Docker build failed: {error_msg}")
            
            return image, logs
            
        except docker.errors.BuildError as e:
            logger.error(f"Docker build failed: {e}")
            for log in e.build_log:
                if 'stream' in log:
                    logger.error(log['stream'])
            raise RuntimeError(f"Docker build failed: {e}")

    async def _build_image(self, app_dir: Path, image_name: str) -> Tuple[Any, List[str]]:
        """Build Docker image from app directory (async wrapper)."""
        # Run blocking Docker build in thread pool to not block event loop
        return await asyncio.to_thread(self._build_image_sync, app_dir, image_name)
    
    def _run_container_sync(
        self, 
        image_name: str, 
        container_name: str, 
        port: int,
        db_schema: str
    ) -> Any:
        """Create and start a container (synchronous)."""
        # Database URL for the container
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?schema={db_schema}"
        
        container = self.docker_client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,
            environment={
                "DATABASE_URL": db_url,
                "PORT": "3000",
                "NODE_ENV": "production",
            },
            ports={
                "3000/tcp": port
            },
            network=DOCKER_NETWORK,
            restart_policy={"Name": "unless-stopped"},
            labels={
                "blueprint.app": "true",
                "blueprint.port": str(port),
            },
            log_config={
                "type": "json-file",
                "config": {
                    "max-size": "10m",
                    "max-file": "3"
                }
            }
        )
        
        return container

    async def _run_container(
        self, 
        image_name: str, 
        container_name: str, 
        port: int,
        db_schema: str
    ) -> Any:
        """Create and start a container (async wrapper)."""
        # Run blocking Docker operation in thread pool
        return await asyncio.to_thread(
            self._run_container_sync, image_name, container_name, port, db_schema
        )
    
    def _check_container_status_sync(self, container) -> Tuple[str, str]:
        """Check container status (synchronous)."""
        container.reload()
        status = container.status
        logs = ""
        try:
            logs = container.logs(tail=50).decode('utf-8')
        except Exception:
            pass
        return status, logs

    async def _wait_for_container(self, container, timeout: int = 60):
        """Wait for container to be running and healthy."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Run blocking Docker operations in thread pool
            status, logs = await asyncio.to_thread(self._check_container_status_sync, container)
            
            if status == "running":
                # Container is running, wait a bit for the app to start
                await asyncio.sleep(5)
                
                # Check if the app is responding
                if "Application is running" in logs or "Listening" in logs.lower():
                    logger.info("Application started successfully")
                    return
                
                # Give it more time
                await asyncio.sleep(2)
                return  # Assume it's ready after running for a bit
                
            elif status == "exited":
                full_logs = await asyncio.to_thread(lambda: container.logs().decode('utf-8'))
                raise RuntimeError(f"Container exited unexpectedly. Logs:\n{full_logs[-2000:]}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"Container did not become ready within {timeout} seconds")
    
    def _run_prisma_push_sync(self, container) -> Tuple[int, str]:
        """Run Prisma db push inside the container (synchronous)."""
        exit_code, output = container.exec_run(
            cmd=["npx", "prisma", "db", "push", "--accept-data-loss"],
            workdir="/app",
            environment={"DATABASE_URL": container.attrs['Config']['Env'][0].split('=', 1)[1]}
        )
        output_str = output.decode('utf-8') if output else ""
        return exit_code, output_str

    async def _run_prisma_push(self, container):
        """Run Prisma db push inside the container."""
        try:
            # Run blocking Docker operation in thread pool
            exit_code, output_str = await asyncio.to_thread(self._run_prisma_push_sync, container)
            
            if exit_code != 0:
                logger.warning(f"Prisma push returned non-zero exit code {exit_code}: {output_str}")
                # Don't fail - the schema might already be in sync
            else:
                logger.info(f"Prisma push completed: {output_str[:500]}")
                
        except Exception as e:
            logger.warning(f"Failed to run Prisma push: {e}")
            # Don't fail deployment - the database might already be set up

    async def get_backend_status(self, app_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the status of a generated backend, including live container status."""
        metadata_file = self.apps_path / str(app_id) / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Check actual container status
        container_name = metadata.get("container_name")
        if container_name:
            try:
                container = self.docker_client.containers.get(container_name)
                metadata["container_status"] = container.status
                if container.status == "running":
                    metadata["status"] = "running"
                elif container.status == "exited":
                    metadata["status"] = "stopped"
            except docker.errors.NotFound:
                metadata["container_status"] = "not_found"
                if metadata.get("status") == "running":
                    metadata["status"] = "stopped"
            except Exception as e:
                logger.warning(f"Failed to get container status: {e}")
        
        return metadata

    async def start_backend(self, app_id: UUID) -> Dict[str, Any]:
        """Start a stopped backend container."""
        metadata = await self.get_backend_status(app_id)
        if not metadata:
            raise FileNotFoundError(f"App {app_id} not found")
        
        container_name = metadata.get("container_name")
        if not container_name:
            # No container exists, need to deploy
            return await self.deploy_backend(app_id)
        
        try:
            container = self.docker_client.containers.get(container_name)
            if container.status != "running":
                container.start()
                await asyncio.sleep(3)  # Wait for startup
                container.reload()
            
            metadata["status"] = "running"
            metadata["container_status"] = container.status
            
            metadata_file = self.apps_path / str(app_id) / "metadata.json"
            self._save_metadata(metadata_file, metadata)
            
            return metadata
            
        except docker.errors.NotFound:
            # Container was removed, redeploy
            return await self.deploy_backend(app_id)
    
    async def stop_backend(self, app_id: UUID) -> Dict[str, Any]:
        """Stop a running backend container."""
        metadata = await self.get_backend_status(app_id)
        if not metadata:
            raise FileNotFoundError(f"App {app_id} not found")
        
        container_name = metadata.get("container_name")
        if container_name:
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status == "running":
                    container.stop(timeout=10)
                container.reload()
                metadata["container_status"] = container.status
            except docker.errors.NotFound:
                metadata["container_status"] = "not_found"
            except Exception as e:
                logger.warning(f"Failed to stop container: {e}")
        
        metadata["status"] = "stopped"
        
        metadata_file = self.apps_path / str(app_id) / "metadata.json"
        self._save_metadata(metadata_file, metadata)
        
        return metadata

    async def delete_backend(self, app_id: UUID) -> bool:
        """Delete a generated backend and its container."""
        app_dir = self.apps_path / str(app_id)
        
        # First, stop and remove the container
        metadata = await self.get_backend_status(app_id)
        if metadata:
            container_name = metadata.get("container_name")
            if container_name:
                await self._stop_container(container_name)
            
            # Remove the image
            image_name = metadata.get("image_name")
            if image_name:
                try:
                    self.docker_client.images.remove(image_name, force=True)
                    logger.info(f"Removed image {image_name}")
                except Exception as e:
                    logger.warning(f"Failed to remove image {image_name}: {e}")
        
        # Remove the app directory
        if app_dir.exists():
            shutil.rmtree(app_dir)
            logger.info(f"Deleted backend for app {app_id}")
            return True
        
        return False
    
    async def restart_backend(self, app_id: UUID) -> Dict[str, Any]:
        """Restart a backend container."""
        metadata = await self.get_backend_status(app_id)
        if not metadata:
            raise FileNotFoundError(f"App {app_id} not found")
        
        container_name = metadata.get("container_name")
        if container_name:
            try:
                container = self.docker_client.containers.get(container_name)
                container.restart(timeout=10)
                await asyncio.sleep(5)  # Wait for restart
                container.reload()
                metadata["status"] = "running"
                metadata["container_status"] = container.status
                
                metadata_file = self.apps_path / str(app_id) / "metadata.json"
                self._save_metadata(metadata_file, metadata)
                
                return metadata
            except docker.errors.NotFound:
                # Container was removed, redeploy
                return await self.deploy_backend(app_id)
        
        # No container, deploy
        return await self.deploy_backend(app_id)

