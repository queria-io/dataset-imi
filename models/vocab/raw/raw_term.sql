{# コア語彙の語（data/imi/term.csv）。取得したままの形 #}

select *
from read_csv('data/imi/term.csv', header = true, all_varchar = true, filename = true)
