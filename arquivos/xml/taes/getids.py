import glob
arquivos = [f for f in glob.glob("*.xml")]
filename = open('idlattes.txt','w')
for arquivo in arquivos:
    filename.write(arquivo.replace('.xml','')+ '\n')
filename.close()
