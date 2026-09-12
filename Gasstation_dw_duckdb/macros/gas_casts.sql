{% macro gas_text(c) -%}
nullif(trim(cast({{ c }} as varchar)), '')
{%- endmacro %}

{% macro gas_id(c) -%}
case when regexp_full_match({{ gas_text(c) }}, '[0-9]+')
     then try_cast({{ gas_text(c) }} as bigint) end
{%- endmacro %}

{% macro gas_num(c) -%}
try_cast({{ gas_text(c) }} as decimal(24,6))
{%- endmacro %}

{% macro gas_ts(c) -%}
try_strptime({{ gas_text(c) }}, [
  '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
  '%Y-%m-%d %H:%M', '%Y-%m-%d',
  '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'
])
{%- endmacro %}

{% macro gas_meta(file, pk) -%}
'gas_station_csv' as source_system,
'{{ file }}' as source_file,
{{ gas_text(pk) }} as source_record_id_raw,
to_json(s) as source_payload,
md5(cast(to_json(s) as varchar)) as raw_record_hash
{%- endmacro %}
