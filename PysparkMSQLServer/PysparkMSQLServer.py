from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, when, isnan, corr
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import RegressionEvaluator, BinaryClassificationEvaluator
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import pyodbc

server = ''
database = ''
username = ''
password = ''
conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

spark = SparkSession.builder \
    .appName("GitHub Portfolio Project") \
    .getOrCreate()

file_path = "path/to/your/data.csv"
df = spark.read.csv(file_path, header=True, inferSchema=True)

df.printSchema()
df.show(5)

null_counts = df.select([count(when(col(c).isNull() | isnan(c), c)).alias(c) for c in df.columns])
null_counts.show()

imputed_df = df.na.fill(df.agg({col: 'mean' for col in df.columns}).first().asDict())

df_filtered = imputed_df.select("column1", "column2", "column3").filter(col("column1") > 10)

df_grouped = df_filtered.groupBy("column2").agg(
    avg("column1").alias("average_column1"),
    count("column3").alias("count_column3")
)

df_grouped.show()

df.describe().show()

corr_matrix = df_filtered.select([corr(c1, c2).alias(f'{c1}_{c2}') for c1 in df_filtered.columns for c2 in df_filtered.columns if c1 != c2])
corr_matrix.show()

pd_corr_matrix = corr_matrix.toPandas()
sns.heatmap(pd_corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
plt.title("Correlation Matrix")
plt.savefig("output/correlation_matrix.png")
plt.show()

df_filtered = df_filtered.withColumn("new_feature", col("column1") * 2)

pd_df = df_grouped.toPandas()

plt.figure(figsize=(10, 6))
plt.bar(pd_df["column2"], pd_df["average_column1"])
plt.xlabel("Column 2")
plt.ylabel("Average Column 1")
plt.title("Average Column 1 by Column 2")
plt.savefig("output/average_column1_by_column2.png")
plt.show()

assembler = VectorAssembler(inputCols=["column1", "new_feature"], outputCol="features")
df_ml = assembler.transform(df_filtered).select("features", col("column3").alias("label"))

train_data, test_data = df_ml.randomSplit([0.7, 0.3], seed=42)

lr = LinearRegression()
lr_model = lr.fit(train_data)

predictions = lr_model.transform(test_data)
evaluator = RegressionEvaluator(metricName="rmse")
rmse = evaluator.evaluate(predictions)
print(f"Root Mean Squared Error (RMSE): {rmse}")

predictions.select("features", "label", "prediction").show(5)

log_reg = LogisticRegression()
log_reg_model = log_reg.fit(train_data)

log_predictions = log_reg_model.transform(test_data)
binary_evaluator = BinaryClassificationEvaluator(metricName="areaUnderROC")
roc_auc = binary_evaluator.evaluate(log_predictions)
print(f"Area Under ROC Curve: {roc_auc}")

log_predictions.select("features", "label", "prediction").show(5)

pd_results = predictions.select("features", "label", "prediction").toPandas()
log_pd_results = log_predictions.select("features", "label", "prediction").toPandas()

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
IF OBJECT_ID('regression_predictions', 'U') IS NOT NULL
  DROP TABLE regression_predictions
CREATE TABLE regression_predictions (
  features NVARCHAR(MAX),
  label FLOAT,
  prediction FLOAT
)
""")

cursor.execute("""
IF OBJECT_ID('classification_predictions', 'U') IS NOT NULL
  DROP TABLE classification_predictions
CREATE TABLE classification_predictions (
  features NVARCHAR(MAX),
  label FLOAT,
  prediction FLOAT
)
""")

for index, row in pd_results.iterrows():
    cursor.execute("INSERT INTO regression_predictions (features, label, prediction) VALUES (?, ?, ?)", row.features, row.label, row.prediction)

for index, row in log_pd_results.iterrows():
    cursor.execute("INSERT INTO classification_predictions (features, label, prediction) VALUES (?, ?, ?)", row.features, row.label, row.prediction)

conn.commit()
conn.close()

pd_results.to_csv("output/regression_predictions.csv", index=False)
log_pd_results.to_csv("output/classification_predictions.csv", index=False)

spark.stop()
