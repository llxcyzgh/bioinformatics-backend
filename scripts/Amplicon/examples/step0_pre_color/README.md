# step0_pre_color 示例数据

## 输入文件

- `group.list` - 样本分组（Tab：样本ID、组名）
- `group_col.list` - 预生成的颜色配置（参考输出格式）

## 测试命令

```bash
bash "${AMPLICON_ROOT}/v2/scripts/step0_pre_color.sh" \
    -i "${AMPLICON_ROOT}/v2/examples/step0_pre_color/group.list" \
    -o PreColor_Output/
```

## 说明

多数 Step 4/5 脚本会在内部调用 `color_defined.pl` 自动生成颜色配置；本模块用于单独预生成 `group_col.list`。
