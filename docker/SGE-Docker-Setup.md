# SGE (Sun Grid Engine) Docker 环境搭建指南

## 最终方案

使用 `drmaa/gridengine` 镜像，通过自定义 entrypoint 脚本解决初始化问题。

## 启动方式

```bash
cd docker
docker compose -f docker-compose.sge.yml up -d
```

查看启动日志确认 health check 通过：

```bash
docker logs sge-master
```

## 提交任务

```bash
# 基本用法
docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qsub your_script.sh'

# 通过共享卷提交（推荐，方便宿主机传递文件）
docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qsub -o /shared /shared/your_script.sh'
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `docker-compose.sge.yml` | Compose 编排，定义容器、端口、卷挂载 |
| `entrypoint-sge.sh` | 自定义启动脚本，处理初始化和配置修复 |
| `../shared/` | 宿主机与容器的共享目录，挂载到容器内 `/shared` |

## 踩坑记录

### 1. 镜像选择

- `agaveapi/gridengine` — Docker v1 格式，新版 Docker 拒绝拉取
- `ohsucompbio/gridengine` — CentOS 6 镜像，在新内核上 SIGSEGV (exit 139)
- `wnameless/sge` — 同样是 Docker v1 格式，拉取失败
- **`drmaa/gridengine` — 最终可用**，基于 Ubuntu，SGE 8.1.9

### 2. Windows Git Bash 路径转换

在 Windows 的 Git Bash 中，`/bin/bash` 会被自动转换为 `C:/Program Files/Git/usr/bin/bash`，导致容器内命令执行失败。

**解决**: 所有 `docker exec` 和 `docker run` 命令前加 `MSYS_NO_PATHCONV=1`，或在 compose 的 `entrypoint` 中使用 `["/bin/bash", "/opt/entrypoint-sge.sh"]` 数组格式绕过。

### 3. hostname 不一致导致 execd 注册失败

镜像默认以 hostname `docker` 执行安装。如果启动容器时用 `-h sge-master`，execd 注册的主机和实际主机名不匹配，队列报 `E` 错误。

**解决**: 保持 `hostname: docker`，与镜像默认配置一致。

### 4. root 用户 gid=0 被 min_gid=100 拒绝

镜像安装后 `min_gid=100`，而 root 的 gid=0。shepherd 启动 job 时检查失败，报错：

```
gid of user root (0) less than minimum allowed in conf (100)
```

导致 job 一直卡在 `qw` 状态，队列进入 QERROR。

**解决**: 在 entrypoint 中直接修改配置文件后重启 qmaster：

```bash
sed -i 's/min_gid.*/min_gid                      0/' /opt/sge/default/spool/master/configuration
/opt/sge/default/common/sgemaster stop
/opt/sge/default/common/sgemaster start
```

不能用 `qconf -mconf global`（会打开 vim 编辑器，非交互模式下失败），也不能用 `qconf -Mconf`（参数被误认为 hostname）。直接改 spool 文件 + 重启是最可靠的方式。

### 5. qmaster 重启后队列进入 au (alarm unknown) 状态

重启 qmaster 后 execd 需要几秒重新注册，期间队列显示 `au`。

**解决**: 正常现象，等待约 10-15 秒后自动恢复，不需要手动干预。

### 6. install.sh 已包含服务启动

镜像的 `install.sh` 会自动启动 qmaster 和 execd。如果在 entrypoint 中再次调用 `sgemaster start` / `sgeexecd start`，会导致重复进程和僵尸进程。

**解决**: 修改配置后需要重启时，先 `stop` 再 `start`，不要重复启动。

## 关键诊断命令

```bash
# 查看队列状态（E = 错误, au = 报警, 空 = 正常）
docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qstat -f'

# 查看 qmaster 日志（排查调度失败原因）
docker exec sge-master bash -c 'tail -20 /opt/sge/default/spool/master/messages'

# 查看 execd 日志（排查 job 执行失败原因）
docker exec sge-master bash -c 'cat /opt/sge/default/spool/execd/docker/messages'

# 清除队列错误状态
docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qmod -cq all.q'

# 查看 job 详细信息
docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qstat -j <JOB_ID>'
```
