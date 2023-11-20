FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml /app/environment.yml

# 콘다 환경이 이미 존재하는지 확인하고, 없다면 새로 만듭니다.
RUN conda env list | grep -q mys2d || conda env create -f environment.yml

# 환경을 활성화하고 작업을 수행합니다.
SHELL ["conda", "run", "-n", "mys2d", "/bin/bash", "-c"]

COPY . /app

EXPOSE 8000

CMD ["conda", "run", "-n", "mys2d", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
