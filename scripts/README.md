# Mantener el perfil

El banner principal está en `assets/banner.svg`. Las portadas de los repositorios están en `assets/projects/`; sus README las enlazan desde este repositorio para compartir el diseño.

`profile.json` configura los tres módulos, la paleta y las descripciones breves de los proyectos. `scripts/update_profile.py` consulta únicamente el listado público de repositorios del usuario, excluye el repositorio del perfil y actualiza `assets/modules.svg` y la sección delimitada por `PUBLIC_REPOS` del README.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_profile.py
```

No necesita paquetes externos. `GITHUB_TOKEN` es opcional para el uso local y permite ampliar el límite de consultas; no se guarda en los archivos generados.

El workflow **Refresh public projects** se ejecuta cada seis horas y también se puede iniciar desde Actions → Run workflow. GitHub puede retrasar los horarios programados y desactivar workflows programados tras periodos prolongados de inactividad en un repositorio público. Solo publica un commit si cambian los archivos generados.
