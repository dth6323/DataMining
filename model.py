import pandas as pd


from mlxtend.frequent_patterns import apriori, association_rules
def data_filter(dataframe, country=False, Country=""):
    if country:
        dataframe = dataframe[dataframe["Country"] == Country]
    return dataframe


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = int(low_limit)
    dataframe.loc[(dataframe[variable] > up_limit), variable] = int(up_limit)


def data_prep(dataframe):
    # Data preprocessing:
    dataframe.dropna(inplace=True)

    # Delete if the product name contains "POST":
    dataframe = dataframe[~dataframe["StockCode"].str.contains("POST", na=False)]

    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]
    dataframe = dataframe[dataframe["Quantity"] > 0]
    dataframe = dataframe[dataframe["Price"] > 0]
    replace_with_thresholds(dataframe, "Quantity")
    replace_with_thresholds(dataframe, "Price")
    return dataframe


def create_invoice_product_df(dataframe, id=False):
    if id:
        return dataframe.groupby(['Invoice', "StockCode"])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)
    else:
        return dataframe.groupby(['Invoice', 'Description'])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)

def check_id(dataframe, stockcode):
    product_name = dataframe[dataframe["StockCode"] == stockcode]["Description"].unique()[0]
    return stockcode, product_name


def apriori_alg(dataframe, support_val=0.01):
    inv_pro_df = create_invoice_product_df(dataframe, id=True)
    frequent_itemsets = apriori(inv_pro_df, min_support=support_val, use_colnames=True)
    rules = association_rules(frequent_itemsets,2, metric="support", min_threshold=support_val)
    sorted_rules = rules.sort_values("support", ascending=False)
    return sorted_rules


def recommend_product(dataframe, product_id, support_val=0.01, num_of_products=5):
    sorted_rules = apriori_alg(dataframe, support_val)
    recommendation_list = []
    for idx, product in enumerate(sorted_rules["antecedents"]):
        for j in list(product):
            if j == product_id:
                recommendation_list.append(list(sorted_rules.iloc[idx]["consequents"])[0])
                recommendation_list = list(dict.fromkeys(recommendation_list))
    return (recommendation_list[0:num_of_products])


def recommendation_system_func(dataframe, support_val=0.01, num_of_products=5):
    product_id = input("Enter a product id:")

    if product_id in list(dataframe["StockCode"].astype("str").unique()):
        product_list = recommend_product(dataframe, int(product_id), support_val, num_of_products)
        if len(product_list) == 0:
            print("There is no product can be recommended!")
        else:
            print("Related products with product id -", product_id, "can be seen below:")

            for i in range(0, len(product_list[0:num_of_products])):
                print(check_id(dataframe, product_list[i]))

    else:
        print("Invalid Product Id, try again!")

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)
df_ = pd.read_excel('./Resource/dataset.xlsx', sheet_name='Year 2010-2011', engine='openpyxl')
df = df_.copy()
df = df.iloc[:10000]
recommendation_system_func(df)
df = data_prep(df)
df = data_filter(df, country=True, Country="Germany")