{# IMI コア語彙で、クラスが持てるプロパティ。1行がクラスとプロパティの組。
   pipelines/imi.py が RDF の owl:Restriction（rdfs:subClassOf の先）から data/imi/class_property.csv に書き出す。 #}

select
    version,
    class_name,
    property_name,
    nullif(value_type, '') as value_type,
    try_cast(nullif(max_cardinality, '') as integer) as max_cardinality
from read_csv('data/imi/class_property.csv', header = true, all_varchar = true)
