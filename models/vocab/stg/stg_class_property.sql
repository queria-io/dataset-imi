{# IMI コア語彙で、クラスが持てるプロパティ。1行がクラスとプロパティの組。
   pipelines/imi.py が RDF の owl:Restriction（rdfs:subClassOf の先）から data/imi/class_property.csv に書き出す。 #}

select
    version,
    class_name,
    property_name,
    nullif(value_type, '') as value_type,
    try_cast(nullif(max_cardinality, '') as integer) as max_cardinality,
    filename as source_path
from {{ ref('raw_class_property') }}
