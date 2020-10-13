#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is the extractLattes script.
#
# Copyright (C) 2017 Vicente Helano
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Vicente Helano <vicente.sobrinho@ufca.edu.br>
# Rafael Perazzo Barbosa Mota <rafael.mota@ufca.edu.br>
# Adaptado do scoreLattes

import sys, time, codecs, re, argparse, csv, requests, os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from unidecode import unidecode
from datetime import date
import csv
import glob
import progressbar
import configparser
import logging
import pandas as pd
import sqlite3
import json
import requests
import time
from geojson import MultiPoint

WORKING_DIR='/usr/src/app/'

config = configparser.ConfigParser()
config.read(WORKING_DIR + 'config.ini')

XML_DIR = WORKING_DIR + str(config['DEFAULT']['xml_dir'])
CSV_DIR = WORKING_DIR + str(config['DEFAULT']['csv_dir'])
HTML_DIR = WORKING_DIR + str(config['DEFAULT']['html_dir'])
logging.basicConfig(filename=WORKING_DIR + 'extractLattes.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',level=logging.ERROR)

def tituloConcluido(formacao,titulo):
    titulos = formacao.findall(titulo)
    if ((titulos==None) or (len(titulos)==0)):
        return 0 #se não tiver o titulo
    for titulo in titulos:
        if (titulo.attrib['ANO-DE-CONCLUSAO']!=""): #Se o titulo estiver concluido
            return (1)
    return (2) #se o titulo estiver em andamento

class Score(object):
    
    def __init__(self, inicio, fim):
        # Período considerado para avaliação
        prefixo = str(config['DEFAULT']['prefixo'])
        self.__arquivo = open(CSV_DIR + prefixo + "producao.csv","w")
        self.__writer = csv.writer(self.__arquivo) #PRODUCAO
        self.__writer.writerow(['tipo','ano','autor','idlattes','titulo','local','identificador','natureza','abrangencia','editora'])
        self.__arquivoProjetos = open(CSV_DIR + prefixo + "projetos.csv","w")
        self.__writerProjetos = csv.writer(self.__arquivoProjetos) #projetos
        self.__writerProjetos.writerow(['tipo','natureza','autor','idlattes','inicio','fim','titulo','graduacao','fomento'])
        self.__arquivoTitulacao = open(CSV_DIR + prefixo + "titulacao.csv","w")
        self.__writerTitulacao = csv.writer(self.__arquivoTitulacao) #titulacao
        self.__writerTitulacao.writerow(['idlattes','nome','graduacao','especializacao','mestrado_profissional','mestrado','doutorado','posdoutorado'])
        self.__arquivoTitulos = open(CSV_DIR + prefixo + "titulos.csv","w")
        self.__writerTitulos = csv.writer(self.__arquivoTitulos) #titulacao
        self.__writerTitulos.writerow(['tipo','nome','inicio','termino','titulo','instituicao','status'])
        self.__numero_identificador = ''
        self.__nome_completo = ''
        self.__instituicao = ''
        self.__codigoInstituicao = ''
        self.__ano_inicio = int(inicio)
        self.__ano_fim = int(fim)
        self.__localizacoes = []
        arquivos = [f for f in glob.glob(XML_DIR + "*.xml")]
        i = 0
        with progressbar.ProgressBar(max_value=len(arquivos)) as bar:
            for arquivo in arquivos:
                tree = ET.parse(arquivo)
                root = tree.getroot()
                self.__curriculo = root
                nome = "INDEFINIDO"
                try:
                    self.__dados_gerais()
                    nome = self.__nome_completo
                    self.__formacao_academica_titulacao()
                    self.__projetos_de_pesquisa()
                    self.__producao_bibliografica()
                    self.__titulos_academicos()
                except Exception as e:
                    logging.error("[" + arquivo + "] " + "[" + nome + "] - " + str(e))
                    continue
                finally:
                    i = i + 1
                    bar.update(i)
        

    def __getLatLon(self,instituicao):
        continuar = str(config['DEFAULT']['localizacoes']).upper()
        if (continuar=="SIM"):
            #requisicao = json.loads(requests.get("https://nominatim.openstreetmap.org/search.php?q=" + instituicao + "&format=json").text)
            requisicao = json.loads(requests.get("https://api.mapbox.com/geocoding/v5/mapbox.places/" + instituicao + ".json?access_token=pk.eyJ1IjoicmFmYWVscGVyYXp6byIsImEiOiJja2ZxcjZ0Z2IwY2FwMnlueWx2ODJuNjBjIn0.V0-g5TeloF0y8XDCzyIm-A").text)
            #time.sleep(1)
            try:
                #latitude = requisicao[0]['lat']
                #longitude = requisicao[0]['lon']
                longitude = requisicao['features'][0]['geometry']['coordinates'][0]
                latitude = requisicao['features'][0]['geometry']['coordinates'][1]
                if (float(longitude),float(latitude)) not in self.__localizacoes:
                    self.__localizacoes.append((float(longitude),float(latitude)))
            except IndexError:
                logging.error(instituicao + " nao encontrada!")

    def __dados_gerais(self):
        if 'NUMERO-IDENTIFICADOR' not in self.__curriculo.attrib:
            raise ValueError
        self.__numero_identificador = self.__curriculo.attrib['NUMERO-IDENTIFICADOR']
        
        dados = self.__curriculo.find('DADOS-GERAIS')
        self.__nome_completo = str(dados.attrib['NOME-COMPLETO']).upper()
        enderecos = self.__curriculo.find('DADOS-GERAIS').findall('ENDERECO')
        for endereco in enderecos:
            self.__instituicao = str(endereco.find('ENDERECO-PROFISSIONAL').attrib['NOME-INSTITUICAO-EMPRESA']).upper()
            self.__codigoInstituicao = str(endereco.find('ENDERECO-PROFISSIONAL').attrib['CODIGO-INSTITUICAO-EMPRESA'])
        #print(self.__numero_identificador,self.__nome_completo,self.__instituicao)

    def __formacao_academica_titulacao(self):
        dados = self.__curriculo.find('DADOS-GERAIS')
        formacao = dados.find('FORMACAO-ACADEMICA-TITULACAO')
        if formacao is None:
            return
        posdoutorado = tituloConcluido(formacao,'POS-DOUTORADO')
        doutorado = tituloConcluido(formacao,'DOUTORADO')
        mestrado = tituloConcluido(formacao,'MESTRADO')
        mestrado_profissional = tituloConcluido(formacao,'MESTRADO-PROFISSIONALIZANTE')
        especializacao = tituloConcluido(formacao,'ESPECIALIZACAO')
        graduacao = tituloConcluido(formacao,'GRADUACAO')
        linha = [self.__numero_identificador,self.__nome_completo,graduacao,especializacao,mestrado_profissional,mestrado,doutorado,posdoutorado]
        self.__writerTitulacao.writerow(linha)
        
        
    def __titulos_academicos(self):
        dados = self.__curriculo.find('DADOS-GERAIS')
        formacao = dados.find('FORMACAO-ACADEMICA-TITULACAO')
        if formacao is None:
            return
        posdoutorados = formacao.findall('POS-DOUTORADO')
        doutorados = formacao.findall('DOUTORADO')
        mestrados = formacao.findall('MESTRADO')
        mestrados_profissional = formacao.findall('MESTRADO-PROFISSIONALIZANTE')
        especializacoes = formacao.findall('ESPECIALIZACAO')
        graduacoes = formacao.findall('GRADUACAO')
        for posdoutorado in posdoutorados:
            linha = ["POS-DOUTORADO",self.__nome_completo,posdoutorado.attrib['ANO-DE-INICIO'],posdoutorado.attrib['ANO-DE-CONCLUSAO'],posdoutorado.attrib['TITULO-DO-TRABALHO'],posdoutorado.attrib['NOME-INSTITUICAO'],"N/A"]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(posdoutorado.attrib['NOME-INSTITUICAO'])
        for doutorado in doutorados:
            linha = ["DOUTORADO",self.__nome_completo,doutorado.attrib['ANO-DE-INICIO'],doutorado.attrib['ANO-DE-CONCLUSAO'],doutorado.attrib['TITULO-DA-DISSERTACAO-TESE'],doutorado.attrib['NOME-INSTITUICAO'],doutorado.attrib['STATUS-DO-CURSO']]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(doutorado.attrib['NOME-INSTITUICAO'])
        for mestrado in mestrados:
            linha = ["MESTRADO ACADEMICO",self.__nome_completo,mestrado.attrib['ANO-DE-INICIO'],mestrado.attrib['ANO-DE-CONCLUSAO'],mestrado.attrib['TITULO-DA-DISSERTACAO-TESE'],mestrado.attrib['NOME-INSTITUICAO'],mestrado.attrib['STATUS-DO-CURSO']]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(mestrado.attrib['NOME-INSTITUICAO'])
        for mestrado_profissional in mestrados_profissional:
            linha = ["MESTRADO PROFISSIONAL",self.__nome_completo,mestrado_profissional.attrib['ANO-DE-INICIO'],mestrado_profissional.attrib['ANO-DE-CONCLUSAO'],mestrado_profissional.attrib['TITULO-DA-DISSERTACAO-TESE'],mestrado_profissional.attrib['NOME-INSTITUICAO'],mestrado_profissional.attrib['STATUS-DO-CURSO']]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(mestrado_profissional.attrib['NOME-INSTITUICAO'])
        for especializacao in especializacoes:
            linha = ["ESPECIALIZACAO",self.__nome_completo,especializacao.attrib['ANO-DE-INICIO'],especializacao.attrib['ANO-DE-CONCLUSAO'],especializacao.attrib['TITULO-DA-MONOGRAFIA'],especializacao.attrib['NOME-INSTITUICAO'],especializacao.attrib['STATUS-DO-CURSO']]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(especializacao.attrib['NOME-INSTITUICAO'])
        for graduacao in graduacoes:
            linha = ["GRADUACAO",self.__nome_completo,graduacao.attrib['ANO-DE-INICIO'],graduacao.attrib['ANO-DE-CONCLUSAO'],graduacao.attrib['TITULO-DO-TRABALHO-DE-CONCLUSAO-DE-CURSO'],graduacao.attrib['NOME-INSTITUICAO'],graduacao.attrib['STATUS-DO-CURSO']]
            self.__writerTitulos.writerow(linha)
            self.__getLatLon(graduacao.attrib['NOME-INSTITUICAO'])
        
    def __projetos_de_pesquisa(self):
        dados = self.__curriculo.find('DADOS-GERAIS')
        if dados.find('ATUACOES-PROFISSIONAIS') is None:
            return

        atuacoes = dados.find('ATUACOES-PROFISSIONAIS').findall('ATUACAO-PROFISSIONAL')
        for atuacao in atuacoes:
            atividade = atuacao.find('ATIVIDADES-DE-PARTICIPACAO-EM-PROJETO')
            if atividade is None:
                continue

            participacoes = atividade.findall('PARTICIPACAO-EM-PROJETO')
            for participacao in participacoes:
                projetos = participacao.findall('PROJETO-DE-PESQUISA')
                if projetos is None:
                    continue

                # O ano de início da participação em um projeto
                inicio_part = int(participacao.attrib['ANO-INICIO'])

                for projeto in projetos:

                    natureza = projeto.attrib['NATUREZA']
                    if natureza not in ['PESQUISA', 'DESENVOLVIMENTO','ENSINO','EXTENSAO']:
                        continue

                    # INICIO: Ignorar projeto ou participação em projeto iniciados após o período estipulado
                    if projeto.attrib['ANO-INICIO'] != "":
                        if int(projeto.attrib['ANO-INICIO']) > self.__ano_fim:
                            continue
                    else:
                        if inicio_part > self.__ano_fim:
                            continue

                    # FIM: Ignorar projeto ou participação em projeto finalizados antes do período estipulado
                    if projeto.attrib['ANO-FIM'] != "":
                        if int(projeto.attrib['ANO-FIM']) < self.__ano_inicio:
                            continue
                    else:
                        if participacao.attrib['ANO-FIM'] != "":
                            fim_part = int(participacao.attrib['ANO-FIM'])
                            if fim_part < self.__ano_inicio:
                                continue

                    # Ignorar se o proponente não for o coordenador do projeto
                    equipe = (projeto.find('EQUIPE-DO-PROJETO')).find('INTEGRANTES-DO-PROJETO')
                    if equipe.attrib['FLAG-RESPONSAVEL'] != str('SIM'):
                        continue

                    # Verifica se o projeto é financiado
                    financiamento = projeto.find('FINANCIADORES-DO-PROJETO')
                    '''
                    if financiamento is None:
                        continue
                    '''
                    # Verifica se há órgão financiador externo, diferente de UFC e UFCA
                    codigos = ['', 'JI7500000002', '001500000997', '008900000002']
                    #financiadores = financiamento.findall('FINANCIADOR-DO-PROJETO')
                    fomento_externo = False
                    if financiamento is not None:
                        financiadores = financiamento.findall('FINANCIADOR-DO-PROJETO')
                        for financiador in financiadores:
                            if financiador.attrib['CODIGO-INSTITUICAO'] not in codigos:
                                fomento_externo = True
                                #break
                    try:
                        anoInicio = int(projeto.attrib['ANO-INICIO'])
                    except ValueError:
                        anoInicio = 0
                    try:
                        anoFim = int(projeto.attrib['ANO-FIM'])
                    except ValueError:
                        anoFim = "Atual"    
                    nomeProjeto = str(projeto.attrib['NOME-DO-PROJETO'])
                    try:
                        estudantes = int(projeto.attrib['NUMERO-GRADUACAO'])
                    except ValueError:
                        estudantes = 0;
                    fomento = 0
                    if not fomento_externo:
                        fomento = 0
                    else:
                        fomento = 1
                    linha = ["PROJETO",natureza,self.__nome_completo,self.__numero_identificador,anoInicio,anoFim,nomeProjeto,estudantes,fomento]
                    self.__writerProjetos.writerow(linha)                    
                     

    def __producao_bibliografica(self):
        producao = self.__curriculo.find('PRODUCAO-BIBLIOGRAFICA')
        if producao is None:
            return

        self.__artigos_publicados(producao)
        self.__trabalhos_em_eventos(producao)
        self.__livros_e_capitulos(producao)
        #self.__demais_tipos_de_producao(producao)

    def __artigos_publicados(self, producao):
        artigos = producao.find('ARTIGOS-PUBLICADOS')
        if artigos is None:
            return

        for artigo in artigos.findall('ARTIGO-PUBLICADO'):
            dados = artigo.find('DADOS-BASICOS-DO-ARTIGO')
            detalhamento = artigo.find('DETALHAMENTO-DO-ARTIGO')
            ano = int(dados.attrib['ANO-DO-ARTIGO'])
            titulo = str(dados.attrib['TITULO-DO-ARTIGO'])
            periodico = str(detalhamento.attrib['TITULO-DO-PERIODICO-OU-REVISTA'])
            issn = str(detalhamento.attrib['ISSN'])
            if (ano>=self.__ano_inicio) and (ano<=self.__ano_fim):
                linha = ["PERIODICOS",ano,self.__nome_completo,self.__numero_identificador,titulo,periodico,issn,"N/A","N/A","N/A"]
                self.__writer.writerow(linha)
        
            
    
    def __trabalhos_em_eventos(self, producao):
        trabalhos = producao.find('TRABALHOS-EM-EVENTOS')
        if trabalhos is None:
            return
        for trabalho in trabalhos.findall('TRABALHO-EM-EVENTOS'):
            
            ano = int(trabalho.find('DADOS-BASICOS-DO-TRABALHO').attrib['ANO-DO-TRABALHO'])
            if ano < self.__ano_inicio or ano > self.__ano_fim: # skip papers out-of-period
                continue
            titulo = str(trabalho.find('DADOS-BASICOS-DO-TRABALHO').attrib['TITULO-DO-TRABALHO'])
            abrangencia = str(trabalho.find('DETALHAMENTO-DO-TRABALHO').attrib['CLASSIFICACAO-DO-EVENTO'])
            natureza = str(trabalho.find('DADOS-BASICOS-DO-TRABALHO').attrib['NATUREZA'])
            evento = str(trabalho.find('DETALHAMENTO-DO-TRABALHO').attrib['NOME-DO-EVENTO'])
            isbn = str(trabalho.find('DETALHAMENTO-DO-TRABALHO').attrib['ISBN'])
            editora = str(str(trabalho.find('DETALHAMENTO-DO-TRABALHO').attrib['NOME-DA-EDITORA']))
            linha = ["ANAIS DE EVENTOS",ano,self.__nome_completo,self.__numero_identificador,titulo,natureza,abrangencia,evento,isbn,editora]
            
            self.__writer.writerow(linha)
        

    def __livros_e_capitulos(self, producao):
        itens = producao.find('LIVROS-E-CAPITULOS')
        if itens is None:
            return
        livros = itens.find('LIVROS-PUBLICADOS-OU-ORGANIZADOS')
        if livros != None:
            for livro in livros.findall('LIVRO-PUBLICADO-OU-ORGANIZADO'):
                ano = int(livro.find('DADOS-BASICOS-DO-LIVRO').attrib['ANO'])
                if ano < self.__ano_inicio or ano > self.__ano_fim: # skip out-of-allowed-period production
                    continue
                if livro.find('DETALHAMENTO-DO-LIVRO').attrib['NUMERO-DE-PAGINAS'] == "":
                    continue
                paginas = 0
                try:
                    paginas = int(livro.find('DETALHAMENTO-DO-LIVRO').attrib['NUMERO-DE-PAGINAS'])
                except ValueError:
                    paginas = 0
                if paginas > 49: # número mínimo de páginas para livros publicados e traduções
                    tipo = livro.find('DADOS-BASICOS-DO-LIVRO').attrib['TIPO']
                    titulo = str(livro.find('DADOS-BASICOS-DO-LIVRO').attrib['TITULO-DO-LIVRO'])
                    editora = str(livro.find('DETALHAMENTO-DO-LIVRO').attrib['NOME-DA-EDITORA'])
                    isbn = str(livro.find('DETALHAMENTO-DO-LIVRO').attrib['ISBN'])
                    linha = [tipo,ano,titulo,paginas,editora,isbn,"N/A"]
                    linha = [tipo,ano,self.__nome_completo,self.__numero_identificador,titulo,"N/A",isbn,"N/A","N/A","N/A"]
                    self.__writer.writerow(linha)
            


        capitulos = itens.find('CAPITULOS-DE-LIVROS-PUBLICADOS')
        if capitulos != None:
            for capitulo in capitulos.findall('CAPITULO-DE-LIVRO-PUBLICADO'):
                if capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['ANO'] == "":
                    continue
                ano = int(capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['ANO'])
                if ano < self.__ano_inicio or ano > self.__ano_fim: # skip out-of-allowed-period production
                    continue
                tipo = capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['TIPO']
                titulo = str(capitulo.find('DADOS-BASICOS-DO-CAPITULO').attrib['TITULO-DO-CAPITULO-DO-LIVRO'])
                editora = str(capitulo.find('DETALHAMENTO-DO-CAPITULO').attrib['NOME-DA-EDITORA'])
                isbn = str(capitulo.find('DETALHAMENTO-DO-CAPITULO').attrib['ISBN'])
                titulo_livro = str(capitulo.find('DETALHAMENTO-DO-CAPITULO').attrib['TITULO-DO-LIVRO'])
                linha = [tipo,ano,self.__nome_completo,self.__numero_identificador,titulo,titulo_livro,isbn,"N/A","N/A","N/A"]
                self.__writer.writerow(linha)
        

    def finalizar(self):
        self.__arquivo.close()
        self.__arquivoProjetos.close()  
        self.__arquivoTitulos.close()
        self.__arquivoTitulacao.close()

    def __csv2sqlite(self,arquivo,tabela):
        df = pd.read_csv(arquivo)
        conn = sqlite3.connect(CSV_DIR + 'extractLattes.sqlite3')
        df.to_sql(tabela, conn, if_exists='replace', index = False)
        conn.close()

    def __csv2ajax(self,arquivo,saida):
        try:
            arquivo_csv = open(arquivo,'r')
            arquivo_txt = open(saida,'w')
            linhas = csv.reader(arquivo_csv,delimiter=',')
            dados = []
            for linha in linhas:
                dados.append(linha)
            del dados[0]
            ajax = {"data": dados}
            arquivo_txt.write(json.dumps(ajax))
        except Exception as e:
            logging.error(str(e))
        finally:
            arquivo_txt.close()
            arquivo_csv.close()

    def exportar(self):
        prefixo = str(config['DEFAULT']['prefixo'])
        self.__csv2sqlite(CSV_DIR + prefixo + "producao.csv","producao")
        self.__csv2sqlite(CSV_DIR + prefixo + "projetos.csv","projetos")
        self.__csv2sqlite(CSV_DIR + prefixo + "titulacao.csv","titulacao")
        self.__csv2sqlite(CSV_DIR + prefixo + "titulos.csv","titulos")
        self.__csv2ajax(CSV_DIR + prefixo + "producao.csv",HTML_DIR + prefixo + "producao.txt")
        self.__csv2ajax(CSV_DIR + prefixo + "projetos.csv",HTML_DIR + prefixo + "projetos.txt")
        self.__csv2ajax(CSV_DIR + prefixo + "titulacao.csv",HTML_DIR + prefixo + "titulacao.txt")
        self.__csv2ajax(CSV_DIR + prefixo + "titulos.csv",HTML_DIR + prefixo + "titulos.txt")

    def salvarLocalizacoes(self):
        prefixo = str(config['DEFAULT']['prefixo'])
        continuar = str(config['DEFAULT']['localizacoes']).upper()
        if (continuar=="SIM"):
            try:
                arquivo = open(HTML_DIR + prefixo + "geo.json",'w')
                arquivo.write(str(MultiPoint(self.__localizacoes)))
            except Exception as e:
                logging.error("SalvarLocalizacoes: " + str(e))
            finally:
                arquivo.close()
        

    def get_name(self):
        return self.__nome_completo

    def get_lattes_id(self):
        return self.__numero_identificador

    def get_localizacoes(self):
        return (self.__localizacoes)

def main():
    inicio = int(config['DEFAULT']['inicio'])
    fim = int(config['DEFAULT']['fim'])
    score = Score(inicio, fim)
    score.finalizar()
    score.exportar()
    score.salvarLocalizacoes()
    
    
# Main
if __name__ == "__main__":
    sys.exit(main())
