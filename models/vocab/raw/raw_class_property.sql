{# クラスが持てるプロパティ（data/imi/class_property.csv）。取得したままの形 #}

select *
from read_csv('data/imi/class_property.csv', header = true, all_varchar = true)
