-- class_property の 1 行は (class_name, property_name) で決まる
select class_name, property_name, count(*) as n
from {{ ref('class_property') }}
group by class_name, property_name
having count(*) > 1
