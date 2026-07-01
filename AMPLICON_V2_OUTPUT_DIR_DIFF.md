# 扩增子脚本库 v1 → v2「显式 `-o` 输出目录」变更核查报告

> **分支**：`henry-dev`
> **核查日期**：2026-07-01
> **核查范围**：仅读 `scripts/Amplicon/reference/*.md` 与 `scripts/Amplicon_v2/reference/*.md`（不读 `scripts/*.sh`）
> **关联报告**：`SCRIPT_CODEGEN_DUAL_PATH_ANALYSIS.md`（脚本链编排双路生成逻辑分析）

---

## 1. 背景（客户为什么改）

客户手工放入 `scripts/Amplicon_v2/`，是对原 `scripts/Amplicon/` 的一轮改进，核心改动一句话：

> **统一给每个脚本增加 `-o <输出目录>` 参数，让产物路径从脚本外部可知、可控。**

原版（v1）的问题有三层：

1. **一部分脚本根本没有 `-o`** —— 产物写到硬编码路径（往往是脚本内部 CWD 或某个固定目录），编排器从外部**无法得知产物落在哪**。
2. **一部分脚本「名义上有 `-o`，实际没起作用」** —— README 里写着 `-o`，但脚本本体没真正实现，调用方照着 README 拼链子就会断。
3. 上述两种情况叠加，导致「自动生成脚本链」时，**上一步产物的路径无法准确接到下一步的输入参数上**——这正是客户提交 v2 要解决的根本痛点。

---

## 2. 核查方法

随机抽取 6 个覆盖各阶段的脚本（预处理 / 核心 / 多样性 / 统计 / 系统发育），在 v1、v2 两套 `reference/*.md` 中分别检索 `-o` / `输出目录` / `--output` 相关行，逐对比对：

| 抽样脚本 | 阶段 |
|---|---|
| `step1_cutadapt` | Step 1 数据预处理 |
| `step3_dada2` | Step 3 ASV 推断（核心） |
| `step3_taxonomy` | Step 3 物种注释 |
| `step3_phylogeny` | Step 3 系统发育树 |
| `step4_lefse` | Step 4 差异分析 |
| `step5_pcoa` | Step 5 排序分析 |

---

## 3. 核查结论：v2 确实系统性地补齐了 `-o`

### 3.1 逐脚本对照

| 脚本 | v1 的 `.md` 是否有 `-o` | v2 的 `.md` 是否有 `-o` | v2 输出目录约定 |
|---|---|---|---|
| `step1_cutadapt` | ❌ 无 | ✅ `-o, --output \| 输出目录 \| 是` | `Cutadapt_Output/` |
| `step3_dada2` | ❌ 无 | ✅ `-o, --output \| 输出目录 \| 是` | `DADA2_Output/` |
| `step3_taxonomy` | ❌ 无 | ✅ `-o, --output \| 输出目录 \| 是` | `Taxonomy_Output/` |
| `step3_phylogeny` | ❌ 无 | ✅ `-o, --output \| 输出目录 \| 是` | `Phylogeny_Output/` |
| `step4_lefse` | ❌ 无 | ✅ `-o, --output \| 输出目录 \| 是` | `LEfSe_Output/` |
| `step5_pcoa` | ❌ 无 | ✅ 全部输出写入 `-o` 指定目录 | `PCoA_Output/` |

**结论：6 个抽样脚本，v1 全部没有 `-o`，v2 全部补齐为「必需」参数。** 客户所述「加了 `-o` 参数」属实。

v2 还形成了一条**统一命名约定**：`<ToolName>_Output/`（如 `Cutadapt_Output/`、`DADA2_Output/`、`PCoA_Output/`…），且每个 `.md` 都显式注释「输出目录：Xxx_Output/；文件：…」，产物文件名**相对输出目录**给出。

### 3.2 铁证：v1 自己就「表里不一」（即客户说的「名义上有 -o 却不生效」）

核查中发现一个关键现象，正好对应客户描述的第 2 层问题：

- v1 的 **`README.md` 第 140–156 行**确实**广告式地**写着 `-o`，例如：
  ```
  bash "${AMPLICON_ROOT}/scripts/step1_cutadapt.sh" -i input.fastq.gz -o Cutadapt_Output/ -f F_PRIMER -r R_PRIMER
  bash "${AMPLICON_ROOT}/scripts/step3_dada2.sh" -m manifest.tsv -o DADA2_Output/
  bash "${AMPLICON_ROOT}/scripts/step3_taxonomy.sh" -i DADA2_Output/featureSeqs.qza -o Taxonomy_Output/ -t 16S
  ```
- 但 v1 的**各工具独立 `.md`**（`step1_cutadapt.md`、`step3_dada2.md`、`step3_taxonomy.md`…）里**完全没有 `-o` 参数的文档**——参数表里没有，调用示例里也没有。
- v1 全库只有 **`step0_import_fasta.md`** 和 **`step4_krona.md`** 真正把 `-o` 写进了参数表。

也就是说：**README 声称全用 `-o`，但绝大多数脚本的参考文档（以及脚本本体）并没有真正实现 `-o`。** 这就是「名义上有 `-o`、实际不生效」的根源——README 与脚本实现脱节。v2 把 README 的承诺落到了**每一个** `.md` 的参数表里，消除了这层不一致。

> 旁证：v1 README 自报版本 `v2.0 / 2026-04-15 / 35 模块`；v2 README 自报 `v2.1（显式 -o 输出目录）/ 2026-06-24 / 37 模块`。版本号与「显式 -o」的副标题直接点明本轮改动主题。

---

## 4. v2 的其它结构性变化（顺便记录）

| 项 | v1 | v2 |
|---|---|---|
| 脚本路径前缀 | `${AMPLICON_ROOT}/scripts/step*.sh` | `${AMPLICON_ROOT}/v2/scripts/step*.sh`（多一层 `v2/`） |
| 新增模块 | — | `step0_pre_color`（分组颜色配置）、`step3_convert_table`（TSV/BIOM→QIIME2） |
| 移除模块 | `step5_dca` | — |
| 模块总数 | 35 | 37 |
| README 全流程示例 | 无完整串联 | 有「场景 2」完整 35 步串联，**每步都带 `-o "${PROJECT}/0X_*/`，下一步 `-i` 指向上一步 `-o` 目录里的具体文件** |

v2 README 还专门强调一条对编排器极其重要的约定：

> **统一约定：全部 37 个脚本均要求 `-o output_dir`。主输入参数不统一——不能默认所有模块都用 `-i`。**

并给出「主输入参数分类表」（`-i` / `-t` / `-e` / `-m` / `-r1 -r2 -f -r` / `-1 -2` / 多文件组合），还提醒 `-t` 在不同脚本里含义不同（table / 16S-18S-ITS 类型 / taxonomy 文件）。

---

## 5. 对「脚本链自动生成」的意义（与第二份报告的衔接）

v1 的 `-o` 缺失，正是编排器接不上链子的根因之一：

- **v1**：产物路径要么硬编码、要么名义上有 `-o` 实则失效。编排器无法可靠推断「`step3_dada2` 的 `featureSeqs.qza` 到底在哪」，只能靠**猜文件名**或假设「都落在当前目录」。一旦猜错，`step3_taxonomy -i featureSeqs.qza` 就找不到文件。
- **v2**：每步强制 `-o <Tool>_Output/`，产物路径变成**确定性的、可拼接的**：`step3_taxonomy -i DADA2_Output/featureSeqs.qza -o Taxonomy_Output/`。编排器只要记住「上一步的输出目录变量」，下一步的 `-i` 就能稳定拼出来。

换言之，**v2 把「产物路径」从脚本内部的隐式知识，变成了脚本接口上的显式契约**——这正是自动化编排最需要的东西。

> 至于当前两条编排链（算法 / LLM）各自为什么还接不稳 v2，以及 LLM 生成为什么「啰嗦」，见 `SCRIPT_CODEGEN_DUAL_PATH_ANALYSIS.md`。

---

## 附录：核查用的命令证据（可复现）

```bash
# v1 各工具 .md 是否提到 -o / 输出目录（6 个抽样全为空）
for f in step1_cutadapt step3_dada2 step5_pcoa step4_lefse step3_taxonomy step3_phylogeny; do
  grep -nE '\-o|\-\-out|输出目录|输出路径' Amplicon/reference/$f.md
done

# v2 同样检索（6 个抽样全部命中 -o）
for f in step1_cutadapt step3_dada2 step5_pcoa step4_lefse step3_taxonomy step3_phylogeny; do
  grep -nE '\-o|\-\-out|输出目录|输出路径' Amplicon_v2/reference/$f.md
done

# v1 README 广告 -o、但 .md 没落地的「表里不一」证据
grep -n '\-o ' Amplicon/reference/README.md        # 命中 140-156 多行
grep -rn '\-o,' Amplicon/reference/step*.md        # 仅 step0_import_fasta、step4_krona 命中

# 两套 reference 的文件清单差异
diff <(ls Amplicon/reference) <(ls Amplicon_v2/reference)
# > step0_pre_color.md, > step3_convert_table.md, < step5_dca.md
```
