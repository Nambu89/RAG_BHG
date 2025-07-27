# 🐳 BHG RAG - Development Container

Este directorio contiene la configuración del Development Container para el proyecto BHG RAG.

## 🚀 Inicio Rápido

### Requisitos
- Docker Desktop
- Visual Studio Code
- Extensión "Dev Containers" para VS Code

### Uso

1. **Abrir en DevContainer**:
   - Abre VS Code
   - `Ctrl/Cmd + Shift + P` → "Dev Containers: Reopen in Container"
   - Espera a que se construya el contenedor (primera vez ~5-10 min)

2. **El contenedor incluye**:
   - Python 3.11
   - Todas las dependencias del proyecto
   - Extensiones de VS Code preconfiguradas
   - Modelos de spaCy preinstalados
   - Git, GitHub CLI, y herramientas de desarrollo

## 📁 Estructura

```
.devcontainer/
├── devcontainer.json    # Configuración principal
├── Dockerfile          # Imagen del contenedor
├── post-create.sh      # Script de inicialización
└── README.md          # Este archivo
```

## ⚙️ Personalización

### Añadir extensiones de VS Code
Edita `devcontainer.json` y añade el ID de la extensión en la sección `extensions`.

### Cambiar recursos
Modifica `runArgs` en `devcontainer.json`:
```json
"runArgs": [
    "--memory=16g",  // Más memoria
    "--cpus=8"       // Más CPUs
]
```

### Variables de entorno
Añade en `containerEnv` en `devcontainer.json`:
```json
"containerEnv": {
    "MI_VARIABLE": "valor"
}
```

## 🔧 Solución de Problemas

### El contenedor no inicia
1. Verifica que Docker Desktop esté ejecutándose
2. Limpia contenedores antiguos: `docker system prune -a`
3. Reconstruye: `Ctrl/Cmd + Shift + P` → "Dev Containers: Rebuild Container"

### Faltan permisos
- El contenedor ejecuta como usuario `vscode` (UID 1000)
- Para comandos root: `sudo comando`

### Performance lento
- Aumenta recursos de Docker Desktop
- En Windows: usa WSL2
- En Mac: asigna más memoria en Docker Desktop

## 📊 Recursos del contenedor

- **Memoria**: 8GB (recomendado 16GB)
- **CPUs**: 4 cores
- **Almacenamiento**: ~5GB para la imagen base

## 🔐 Seguridad

- Las claves SSH se montan desde tu máquina local
- El archivo `.env` NO se incluye en la imagen
- Usa secretos de VS Code para datos sensibles

## 🛠️ Comandos útiles

```bash
# Ver logs del contenedor
docker logs <container-id>

# Ejecutar comando en el contenedor
docker exec -it <container-id> bash

# Limpiar todo y empezar de nuevo
docker system prune -a --volumes
```

## 📚 Referencias

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [devcontainer.json reference](https://containers.dev/implementors/json_reference/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)