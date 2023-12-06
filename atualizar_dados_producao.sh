#!/bin/bash
cd ../postgres
rm -f python/xml/*.xml
docker-compose run --rm python3 python /python/idlattes_docentes.py
cd ../lattes
docker-compose run --rm scorelattes
cd arquivos/csv/docentes
sqlite3 extractLattes.sqlite3 'select ano,tipo,count(*) from producao group by tipo,ano ORDER BY ano,tipo;' > resultado.txt
cd ~/docker/projetos/lattes
clear
