import pandas as pd
import pandasql as ps

# Lendo o arquivo csv
df = pd.read_csv('qualis-periodicos-2017.csv')
print(ps.sqldf("SELECT * FROM df WHERE ISSN='2236-2029';", locals()))