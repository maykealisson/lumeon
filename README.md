### Cria ambiente

python -m venv .venv
source .venv/bin/activate

### Ativa ambiente toda vez que for rodar projeto

source .venv/bin/activate

### Instale as dependencias

pip install -r requirements.txt

### Gerar img docker

```
docker buildx build --platform=linux/arm64/v8 -t maykealisson/agent-fundament:{{VERSION}} .
```

```
docker push maykealisson/agent-fundament:{{VERSION}}
```
