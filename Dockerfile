FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml /app/environment.yml
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "mys2d", "/bin/bash", "-c"]

COPY . /app

EXPOSE 8000

CMD ["conda", "run", "-n", "mys2d", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
