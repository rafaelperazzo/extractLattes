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
    localizacoes = SIM
```
## Saída

* arquivos CSV com as extrações:
 * Produção Bibliográfica
  * Em periódicos
  * Em anais
  * Livros e capítulos
 * Projetos de pesquisa, extensão, ensino e desenvolvimento
 * Titulação
 * Títulos
* Banco de dados Sqlite3 com todas as informações acima

## Como executar

```
docker-compose run --rm scorelattes python scorerun.py
```

## TODO
* Incluir outras extrações, como vínculos profissionais
* Incluir recurso para avaliação de alunos de IC (PIBIC/PIBITI): Quantos entraram na pós, aumento de produção, etc...

## AGRADECIMENTOS

Ao projeto do Prof. Vicente Helano (UFCA), desenvolvedor do projeto [scoreLattes](https://github.com/vicentehelano/scoreLattes)