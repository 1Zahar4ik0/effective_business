"""Проверка сценариев DATA-API.yaml против запущенного локального приложения."""
import json
from pathlib import Path
import httpx

def pointer(data, path):
    for key in path.strip('/').split('/'):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data

def main():
    spec=json.loads((Path(__file__).resolve().parents[1]/'DATA-API.yaml').read_text(encoding='utf-8'))
    if spec['base_url'] not in ('http://localhost:8000','http://127.0.0.1:8000'):
        raise RuntimeError('Проверка разрешена только на локальном адресе')
    variables={}
    def expand(value):
        if isinstance(value,dict):return {k:expand(v) for k,v in value.items()}
        if isinstance(value,str) and value.startswith('{') and value.endswith('}'):return variables[value[1:-1]]
        return value
    with httpx.Client(base_url=spec['base_url'],headers={'X-App-Request':'1'},timeout=15,trust_env=False) as client:
        for index,step in enumerate(spec['steps'],1):
            path=step['path'].format(**variables)
            response=client.request(step['method'],path,json=expand(step.get('body')), params=step.get('query'),
                                    headers=expand(step.get('headers', {})))
            assert response.status_code==step['expect'],f'{index}: {response.status_code} != {step["expect"]}'
            assert response.headers.get('content-type','').startswith(step['response']['content_type']), f'{index}: content type'
            data=response.json()
            assert isinstance(data, list if step['response']['type']=='array' else dict), f'{index}: response type'
            for field in step['response'].get('required', []):
                assert field in data, f'{index}: required {field}'
            for path,value in step.get('equals',{}).items():assert pointer(data,path)==value,f'{index}: {path}'
            for name,path in step.get('capture',{}).items():variables[name]=pointer(data,path)
            if 'csrf' in variables:client.headers['X-CSRF-Token']=variables['csrf']
            print(f'{index:02d} PASS {step["method"]} {step["path"]}')
    print(f'Пройдено {len(spec["steps"])} шагов DATA-API.yaml')

if __name__=='__main__':main()
