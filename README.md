# DevOps Demo

Project demo implementasi CI/CD otomatis untuk aplikasi web Python Flask menggunakan Jenkins, Docker, Docker Hub, dan Ansible dengan 2 VPS.

Aplikasi memiliki 2 endpoint:
- `GET /` - mengembalikan teks `Hello from DevOps CI/CD!`
- `GET /health` - mengembalikan teks `OK` untuk health check dan monitoring

Container berbasis `python:3.12-slim`, workdir `/app`, expose port `5000`, command `python app.py`. Image dipublish ke Docker Hub `mafifdev/devops-demo` dengan tag `BUILD_NUMBER` dan `latest`.

## Arsitektur 2 VPS

VPS 1 - Jenkins Server - `192.168.123.35`:
- Jenkins (pipeline otomatis)
- Docker (build dan push image)
- Ansible controller (deploy ke VPS 2)
- Kredensial Docker Hub dengan ID `mafifdev`
- Akses SSH ke VPS 2 sebagai user `devops`

VPS 2 - Production Server - `192.168.123.163`:
- Docker Engine
- User `devops` dengan akses SSH dari VPS 1
- Port 80 terbuka untuk akses publik
- Container `devops-demo` berjalan dengan mapping `80:5000` dan restart policy `unless-stopped`

Alur CI/CD:
1. Developer push ke repository
2. Jenkins di VPS 1 checkout source code
3. Stage Test: cek `python3 --version`, `docker --version`, `python3 -m py_compile app.py`
4. Stage Docker Build: `docker build -t mafifdev/devops-demo:$BUILD_NUMBER -t mafifdev/devops-demo:latest .`
5. Stage Docker Push: login Docker Hub, push kedua tag, logout
6. Stage Ansible Deploy: `ansible-playbook -i ansible/inventory ansible/deploy.yml -e image_tag=$BUILD_NUMBER` (pull image, stop dan remove container lama, run container baru, wait port 80)
7. Stage Health Check: `curl -f http://192.168.123.163/health` atau `curl -f http://192.168.123.163/`

## Struktur Project

- `app.py` - source Flask
- `requirements.txt` - dependensi `flask`
- `Dockerfile` - build image production
- `Jenkinsfile` - definisi pipeline 6 stage
- `ansible/inventory` - target `[production] prod-server ansible_host=192.168.123.163 ansible_user=devops`
- `ansible/deploy.yml` - playbook pull, stop, rm, run, wait_for port 80
- `ansible/ansible.cfg` - `host_key_checking=False`, pipelining True

## Prasyarat

- VPS 1: Ubuntu, Jenkins, Docker, Ansible, Java, koneksi internet, SSH key ke VPS 2
- VPS 2: Ubuntu, Docker, user `devops`, port 22 dan 80 terbuka
- Akun Docker Hub `mafifdev`
- Git

## Langkah Penggunaan

### 1. Clone Project

```
git clone <url-repo> devops-demo
cd devops-demo
```

### 2. Jalankan Lokal (tanpa Docker)

Dilakukan di laptop atau VPS 1 untuk development:

```
pip install -r requirements.txt
python app.py
```

Verifikasi:

```
curl http://localhost:5000
curl http://localhost:5000/health
```

### 3. Jalankan dengan Docker (VPS 1 atau VPS 2)

```
docker build -t mafifdev/devops-demo:latest .
docker run -d --name devops-demo --restart unless-stopped -p 80:5000 mafifdev/devops-demo:latest
docker ps
docker logs devops-demo
curl -f http://localhost:80/health
```

Stop dan hapus:

```
docker stop devops-demo
docker rm devops-demo
```

### 4. Setup SSH VPS 1 ke VPS 2 (sekali saja di VPS 1)

```
ssh-keygen -t ed25519
ssh-copy-id devops@192.168.123.163
ssh devops@192.168.123.163 "docker --version"
```

### 5. Deploy Manual dengan Ansible (dari VPS 1)

```
cd devops-demo
export ANSIBLE_CONFIG=ansible/ansible.cfg
ansible -i ansible/inventory production -m ping
ansible-playbook -i ansible/inventory ansible/deploy.yml -e "image_tag=latest"
```

Verifikasi dari VPS 1:

```
curl -f http://192.168.123.163/health
curl -f http://192.168.123.163/
```

### 6. Setup Jenkins Pipeline Otomatis (di VPS 1 `192.168.123.35`)

1. Install plugin: Pipeline, Git, Credentials Binding
2. Tambah Credentials Docker Hub: Kind Username with password, ID `mafifdev`, isi user dan token Docker Hub
3. Buat Job Pipeline baru, arahkan ke repository ini, script path `Jenkinsfile`
4. Pastikan user `jenkins` bisa menjalankan `docker` dan `ansible-playbook`:

```
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
ansible-playbook --version
```

5. Jalankan Build Now, cek console output tiap stage
6. Akses hasil: `http://192.168.123.163/` dan `http://192.168.123.163/health`

## Troubleshooting

- `curl failed`: cek container di VPS 2 `docker ps -a`, `docker logs devops-demo`, pastikan port 80 tidak dipakai
- `permission denied docker`: user belum masuk grup docker, logout lalu login ulang
- `ansible unreachable`: cek `ansible_host`, user, SSH key, dan firewall port 22
- `docker login failed`: cek credentials ID `mafifdev` dan token Docker Hub
- `locale warning`: sudah ditangani di Jenkinsfile dengan `export LC_ALL=C.UTF-8`
