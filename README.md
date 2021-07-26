# andale

https://github.com/celery/celery/blob/e2031688284484d5b5a57ba29cd9cae2d9a81e39/celery/app/base.py#L141
# https://stackoverflow.com/questions/15159394/how-to-monitor-events-from-workers-in-a-celery-django-application

https://ipwhois.readthedocs.io/en/latest/README.html

https://pypi.org/project/pyasn/
https://stackoverflow.com/questions/34754397/can-i-open-a-named-pipe-on-linux-for-non-blocked-writing-in-python/34754523

- https://gist.github.com/oconnor663/08c081904264043e55bf
- https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
- https://gist.github.com/mightymercado/4efba1f070a6ba6526c3e237f0eb0443

```sh
PYTHONPATH=./ python3 src/tasks/docker/__init__.py 
```

- A better json tool
  - https://gist.github.com/abhinav-upadhyay/5300137
- A way to stop/break out of workflow
- Tasks with callback
  - Callback to let us know is complete
    - Lambda
    - ECS
- A way to follow tasks that is implemented at task level
- Every task was a workspace
- A way for tasks to set taskspace kv store
- Inventory automatically generates lists (csv,json)
  - ips
    - all.csv
    - by_group/{{ id }}.csv
  - domains
    - all.csv
    - by_group/{{ id }}.csv
    - by_domain/{{ domain }}
- https://github.com/rezen/awwwdit-www/tree/master/app/Inventory
```yaml
---
params:
  domain:
    type: string
    required: true
vars:
  record_types:
    - CNAME
    - A
  domain: 
  hash: "{{ var.domain | hash }}"
  dnsgen_list: "domain/{{ var.hash }}/dnsgen_list.csv"
  subdomain_list: domain/{{ var.hash }}/subdomains.csv"

executor: local # vs ecs or lambda
tasks:
    - name: dns_a
      task: dns
      params: 
        domain: {{ vars.domain }}
        rtype: "A"
        name_server: 8.8.8.8
      export: {}
      id: "domains/{{ vars.domain | md5 }}/dns_{{ item }}.json"
      loop: ["A", "CNAME", "MX", "TXT"] 

    - task: nmap
      id: "domains/{{ vars.domain | md5 }}/nmap.json"
      params: 
        hosts: {{ vars.domain + tasks.dns_a.data.results }}
        top_ports: 100
        scripts:
            - name: http-title
      export:
        http_services: >
            {{ hosts | jmespath 'services[?service == `http`].port' }}

    - task: http 
      id: "domains/{{ vars.domain | md5 }}/http_port_{{ item.port }}.json"
      params: 
        url: "https://{{ item.port }}"
        method: "get"
      export: {}
      loop: "{{ tasks.nmap.export.http_services }}"
```