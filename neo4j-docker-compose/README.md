  刷新 Neo4j Browser 后再执行：

  MATCH (n) RETURN count(n)

  应该显示 229。

  然后看完整图：

  MATCH (n)-[r]-(m)
  RETURN n, r, m

  ---
  如果还是 0，检查以下几点：

  1. 确认访问的是当前启动的实例
    - 地址：http://localhost:7474
    - 登录：neo4j / bioflow123
  2. 确认 init 容器已执行完成
  docker logs bioflow-neo4j-init
  3. 如果之前用旧数据启动过，需要强制重建
  docker compose down
  docker compose up -d
  docker logs -f bioflow-neo4j-init