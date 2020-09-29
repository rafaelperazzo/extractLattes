# extractLattes
**uma ferramenta de extração de informações do currículo lattes para geração de indicadores e avaliação de programas acadêmicos**
## Requisitos

* [Docker](https://docs.docker.com/get-docker/)
* [Docker-compose](https://docs.docker.com/compose/install/)

## Entrada

* pasta com os XML Lattes a serem extraídos
* configuração do arquivo config.ini (exemplo):

```
    [DEFAULT]
    inicio = 2013
    fim = 2020
    prefixo = DOCENTES_
    xml_dir = xml/
```
## Saída

* arquivos CSV com as extrações:
 * Produção Bibliográfica
  * Em periódicos
  * Em anais
  * Livros e capítulos
 * Projetos de pesquisa
 * Titulação
 * Títulos

## Como executar

```
docker-compose run --rm scorelattes python scorerun.py
```

## TODO
* Exportar para um arquivo Sqlite3 para gerar uma api em PHP com JSON
* Adicionar geolocalização da formação dos pesquisadores
* Incluir outras extrações, como vínculos profissionais e projetos de extensão
* Incluir recurso para avaliação de alunos de IC (PIBIC/PIBITI): Quantos entraram na pós, aumento de produção, etc...

## AGRADECIMENTOS

Ao projeto do Prof. Vicente Helano (UFCA), desenvolvedor do projeto [scoreLattes](https://github.com/vicentehelano/scoreLattes)