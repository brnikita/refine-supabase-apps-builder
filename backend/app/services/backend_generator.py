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
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from uuid import UUID

from app.config import settings
from app.schemas.blueprint import BlueprintV3
from app.services.amplication_converter import AmplicationConverter

logger = logging.getLogger(__name__)

# Base path for generated apps
GENERATED_APPS_PATH = os.getenv("GENERATED_APPS_PATH", "/var/lib/blueprint-apps")

# Port range for generated backends
PORT_RANGE_START = 4001
PORT_RANGE_END = 4999


class BackendGeneratorService:
    """Generates and manages NestJS backends from BlueprintV3."""

    def __init__(self):
        self.converter = AmplicationConverter()
        self.apps_path = Path(GENERATED_APPS_PATH)
        self.apps_path.mkdir(parents=True, exist_ok=True)

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
            
            return {
                "backend_url": f"http://localhost:{port}/api",
                "port": port,
                "status": "generated",
                "path": str(app_dir),
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
        create_dto = self._generate_create_dto(entity_name, table)
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
    const {{ start = 0, end = 10, sort = 'createdAt', order = 'DESC' }} = options;
    const take = end - start;
    const skip = start;
    
    const [data, total] = await Promise.all([
      this.prisma.{entity_lower}.findMany({{
        skip,
        take,
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

    def _generate_create_dto(self, entity_name: str, table) -> str:
        """Generate Create DTO."""
        fields = []
        imports = ["import { ApiProperty } from '@nestjs/swagger';"]
        
        validators = set()
        for col in table.columns:
            decorator = self._get_validator_decorator(col)
            if decorator:
                validators.add(decorator[0])
            
            optional = "" if col.required else "?"
            ts_type = self._to_typescript_type(col.type)
            
            fields.append(f'''
  @ApiProperty({{ required: {str(col.required).lower()} }})
  {col.name}{optional}: {ts_type};''')
        
        if validators:
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
        return '''FROM node:20-alpine

WORKDIR /app

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
        """Allocate a port for the app."""
        # Simple port allocation based on app_id hash
        # In production, this should check for port availability
        hash_val = hash(str(app_id))
        port = PORT_RANGE_START + (abs(hash_val) % (PORT_RANGE_END - PORT_RANGE_START))
        return port

    async def deploy_backend(self, app_id: UUID) -> Dict[str, Any]:
        """
        Build and deploy the generated backend as a Docker container.
        
        Note: This requires Docker to be available.
        """
        app_dir = self.apps_path / str(app_id)
        metadata_file = app_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"App {app_id} not found")
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # In a real implementation, this would:
        # 1. Build Docker image
        # 2. Run container with allocated port
        # 3. Run Prisma migrations
        # 4. Update metadata with container_id
        
        # For now, return the metadata
        metadata["status"] = "ready"
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return metadata

    async def get_backend_status(self, app_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the status of a generated backend."""
        metadata_file = self.apps_path / str(app_id) / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file) as f:
            return json.load(f)

    async def delete_backend(self, app_id: UUID) -> bool:
        """Delete a generated backend and its container."""
        app_dir = self.apps_path / str(app_id)
        
        if app_dir.exists():
            shutil.rmtree(app_dir)
            logger.info(f"Deleted backend for app {app_id}")
            return True
        
        return False

