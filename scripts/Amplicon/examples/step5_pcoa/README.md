# PCoA 示例数据

## 数据来源

- `weighted_unifrac_pc.txt`: `${AMPLICON_ROOT}/examples/step5_pcoa/weighted_unifrac_pc.txt`
- `unweighted_unifrac_pc.txt`: `${AMPLICON_ROOT}/examples/step5_pcoa/unweighted_unifrac_pc.txt`
- `group.list`: `${AMPLICON_ROOT}/examples/step5_pcoa/group.list`

## 测试命令

```bash
cd "${AMPLICON_ROOT}/examples/step5_pcoa"
bash "${AMPLICON_ROOT}/scripts/step5_pcoa.sh" -w weighted_unifrac_pc.txt -wu unweighted_unifrac_pc.txt -g group.list
```

## 输出

- `PCoA/PCoA.pdf`: PCoA 合并排序图（PDF 格式）
- `PCoA/PCoA.png`: PCoA 合并排序图（PNG 格式）
- `PCoA/weighted_unifrac/PCoA12.pdf`: Weighted UniFrac PCoA 图
- `PCoA/weighted_unifrac/PCoA12.png`: Weighted UniFrac PCoA 图
- `PCoA/unweighted_unifrac/PCoA12.pdf`: Unweighted UniFrac PCoA 图
- `PCoA/unweighted_unifrac/PCoA12.png`: Unweighted UniFrac PCoA 图

## 说明

- 分组颜色配置（group_col.list）由脚本内部自动调用 `color_defined.pl` 生成
- 无需手动提供 group_col.list 文件
