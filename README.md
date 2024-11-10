Для автоматизации процесса создания архива GitLab и его загрузки на MEGA.nz

Пользователь уже должен иметь установленный и настроенный https://mega.io/cmd#download и иметь возможность управлять docker

1)
```mega-mkdir /backup && mega-mkdir /backup/gitlab```

2)
```python3 backup_docker_git.py```
