# 脚本链编排「双路生成」逻辑分析报告（算法 vs LLM）

> **分支**：`henry-dev`
> **分析日期**：2026-07-01
> **核心代码**：`pkg/amplicon/orchestrator.py`、`pkg/amplicon/script_registry.py`、`app/services/chat_service.py`
> **关联报告**：`AMPLICON_V2_OUTPUT_DIR_DIFF.md`（v1→v2 `-o` 变更核查）

---

## 0. 一句话结论

当前编排脚本有**两套并行的生成逻辑**，在用户「确认上传」时**同时各跑一遍**做 A/B 对比：

- **算法路（`script1`）**：结构化、确定性，但**写死了 v1「无 `-o`、产物落 CWD」的假设**，接不进 v2 的显式输出目录；
- **LLM 路（`script2`）**：能读参考文档、灵活，但**把整篇 `.md` 原文灌给模型**，又要求它「文件名不匹配就 rename/symlink」，于是**非常啰嗦**。

两者看似不同，根因却是一个：**都没有一份结构化的「工具 I/O 契约」可依**——算法靠硬编码文件名，LLM 靠从散文里猜文件名。v2 的 `-o` 恰恰就是这份缺失的契约。

---

## 1. 双路生成的调用结构

入口在 `ChatService.confirm_upload()`（`app/services/chat_service.py`），用户上传文件校验通过后：

```python
# chat_service.py:1092  ── 算法路
generated_code_algo = generate_orchestrator_script(
    tool_ids=tool_ids, call_defs=call_defs, tool_names=tool_names,
    file_mappings=..., required_files=..., extra_params=..., param_overrides=...,
)
# chat_service.py:1109  ── LLM 路
llm_out = ChatService._generate_orchestrator_with_llm(
    tool_ids=tool_ids, tool_chain=tool_chain, file_mappings=...,
    required_files=..., extra_params=..., param_overrides=...,
)
```

两份结果一并塞进消息负载（`chat_service.py:1129-1135`）：

```python
result_payload = json.dumps({
    "script1": generated_code_algo,   # 算法
    "script2": generated_code_llm,    # LLM
    "status":  {"script1": ..., "script2": ...},
    "errors":  {"script1": algo_error, "script2": llm_error},
}, ...)
```

> 这是一个**对照实验**架构：两条路同题同答，输出并排呈现，方便人眼比选。
>
> 注：还有一个更老的 `_generate_script_with_llm()`（`chat_service.py:958`），它把**每个工具 `.sh` 原文**喂给模型、要求「保留核心逻辑」——更啰嗦，但**当前没有任何调用方**（已是死代码，属旧架构遗留）。本报告聚焦在线的 `_generate_orchestrator_with_llm`。

---

## 2. 算法路：为什么接不稳「硬编码输入输出路径」（即 v2 `-o`）

算法路的入口 `generate_orchestrator_script()`（`orchestrator.py:47`）按 `tool_ids` 顺序拼 bash，每步调一个 `stepX_*.sh`，靠 `produced_files: dict[data_type, filename]` 在步骤间传文件名。它**接不稳 v2** 的原因有三层：

### 2.1 产物被当成「CWD 里的裸文件名」

注册产物时（`orchestrator.py:202`）：

```python
for out in call_def.outputs:
    produced_files[out.data_type] = out.filename.replace("${sample}", "")
```

——只存**裸文件名**（`featureSeqs.qza`、`asv_table.even.txt`…），**没有任何目录前缀**。这隐含假设：脚本把产物写在当前工作目录。这在 v1 恰好成立（v1 脚本无 `-o`，写 CWD），但 v2 每步把产物写进 `-o` 指定的 `<Tool>_Output/`，于是下一步的 `-i` 指向裸文件名时**找不到文件**。

下一步取输入也同理（`_build_single_command`，`orchestrator.py:428-429`）：

```python
if dt in produced:
    cmd_parts.append(f'{param.flag} "{produced[dt]}"')   # 只拼裸文件名
```

### 2.2 `_OUTPUT_DIR` 类型「定义了却不处理」

`script_registry.py` 里**确实**预留了一个 `_OUTPUT_DIR` 数据类型——但**只 `amp-import-fasta` 用了一次**（`script_registry.py:39`）：

```python
ParamDef(flag="-o", data_type="_OUTPUT_DIR", default="Import_Output"),
```

而真正拼命令的 `_build_single_command()`（`orchestrator.py:379`）参数循环里，**只显式处理了** `_CONFIG / _PRIMER_F / _PRIMER_R / _MANIFEST / _METADATA / _GROUP_LIST`（`orchestrator.py:387-419`），**没有 `_OUTPUT_DIR` 分支**。`_OUTPUT_DIR` 掉进了兜底分支（`orchestrator.py:421`）：

```python
if dt.startswith("_"):
    # 其他特殊类型跳过
    if param.default:
        cmd_parts.append(f'{param.flag} {param.default}')
    continue
```

也就是说，import-fasta 能出 `-o Import_Output` 纯属**意外命中兜底分支的 default**；而全库其余所有工具的 `ScriptCallDef` **根本没定义 `-o` 参数**，算法自然**永远不会给它们发 `-o`**。

> 这是「算法写死 v1 假设」最硬的证据：注册表里有表达「输出目录」的能力（`_OUTPUT_DIR`），但生成器没接，注册表里也几乎没人用。

### 2.3 还有两处 tool_id 硬编码的「地雷」

- **per-sample 并行区按字面 tool_id 分发**（`orchestrator.py:331-338`）：只认 `amp-cutadapt / amp-flash / amp-frags-qc` 三个，**其它任何 `per_sample=True` 的工具直接 `raise ValueError`**。一旦往库里加新的 per-sample 脚本（比如客户后续加的），算法编排当场崩。
- **DADA2 步骤被特判**（`orchestrator.py:194` `if tool_id == "amp-dada2"`）：manifest 生成、产物 key（`produced["FEATURE_SEQS"] = "featureSeqs.qza"` 等，`orchestrator.py:374-376`）全是写死的，换一个汇总工具就不适用。

### 2.4 小结

算法路不是「不能生成脚本」，而是它的整个数据流（裸文件名 + 无 `-o` + CWD 假设）**和 v1 的隐式契约是一一绑定的**。换到 v2：

1. v2 脚本**要求** `-o`，算法不发 → 脚本要么报错、要么写到不可控的默认路径；
2. v2 产物在 `<Tool>_Output/` 内，算法却把下一步 `-i` 指向裸文件名 → **文件找不到**。

所以客户「改脚本加 `-o`」之后，算法路如果不跟着改，反而会比 v1 更容易断。

---

## 3. LLM 路：为什么会「非常啰嗦」

入口 `_generate_orchestrator_with_llm()`（`chat_service.py:664`）。啰嗦不是模型随机发挥，而是**输入构造 + 提示词**两方面共同逼出来的。逐条拆：

### 3.1 把整篇 `.md` 原文灌进去（最大元凶）

`_load_tool_reference_md()`（`chat_service.py:639`）直接 `return f.read()`——**完整返回一个工具 `.md` 的全文**，不做任何抽取。每篇 `.md` 约 100–150 行，包含：基本信息表、适用范围、报价分数、输入表、输出表、多个 bash 示例、参数说明表、相关文件……

```python
# chat_service.py:~657
with open(os.path.join(..., candidates[0]), "r", encoding="utf-8") as f:
    return f.read()
```

然后逐工具拼进 prompt（`chat_service.py:687` 一带）：10 个工具 ≈ **1000–1500 行散文/表格/示例**全部喂给模型。后果：
- 模型倾向于**镜像文档的写法**——大段注释、把参数表抄成行内注释、照抄示例命令（连示例里的注释一起抄）；
- 信噪比极低，模型分不清「调用契约」和「说明性文字」。

### 3.2 提示词本身又长又「鼓励铺陈」

`system_prompt`（`chat_service.py:~738` 起）有 **15 条规则**，其中：

- **规则 14** 是一整段并行区模板（`SAMPLES=()` / `MAX_JOBS` / `_JOB_I` / `for … ( … ) &` / `wait`），要求模型**逐字复刻**这套脚手架 → 每个脚本都自带一大段固定骨架；
- **规则 10** 强制每步输出进度日志 `echo "[…] [Step X/N] 正在执行: …"`；
- **规则 4 + 规则 15** 都在说：「文件名不匹配**必须**显式重命名或 symlink」「绝不用 cp 伪造」。

### 3.3 防御性 rename/symlink 满天飞（啰嗦且危险）

规则 4/15 本意是防「文件名对不上」，但**因为 v1 的 `.md` 根本不说产物到底叫什么、落在哪**（见第一份报告），模型**没法确定**上一步产物名和下一步入参名是否一致。稳妥起见它就**到处加 `mv` / `ln -s`** 把名字「对齐」——于是脚本里塞满防御性重命名行，又长又易错。

> 这一点和算法路是同一个病根的两面：**没有结构化的产物文件名契约**。算法是硬编码一个（可能错的）名字；LLM 是不确定名字、于是用 rename 兜底。

### 3.4 没有长度预算 / 没有结构化输出约束

- **没有 `response_format: json_object`**（对比意图识别那一路是有的）——模型纯自由文本输出 bash，没有任何「只输出调用行、别加注释」的硬约束；
- 规则 11 只说「只输出 bash、不要 markdown 代码块」，**没限制长度、没禁止行内注释**；
- `temperature=0.3`（`chat_service.py:~815`）不是啰嗦的主因，但叠加上述几条，模型就放心地写 200+ 行。

### 3.5 LLM 路同样没接 v2

`_AMPLICON_REF_DIR` 写死指向 **v1**（`chat_service.py:751-754`，`scripts/Amplicon/reference`），不是 `Amplicon_v2/reference`。所以 LLM 现在读到的还是「没有 `-o`、产物路径不明」的 v1 文档，第 3.3 节的「猜名字 + 防御性 rename」问题会一直存在。

### 3.6 啰嗦的本质

啰嗦是**症状**，根因是：**LLM 在用自然语言推理一件本该结构化的事**——「上一步产出哪个文件、下一步用哪个 flag 吃它」。给它整篇散文，它就只能边读边猜边兜底，输出自然膨胀。

---

## 4. 共同根因

| | 算法路 | LLM 路 |
|---|---|---|
| 怎么知道产物路径 | 硬编码裸文件名（`produced[dt] = out.filename`） | 从 `.md` 散文里猜 |
| 怎么知道下一步入参 | 按 `data_type` 查 `produced`（裸名） | 从 `.md` 散文里猜 + rename 兜底 |
| 是否消费 `-o` 契约 | 否（注册表几乎没 `-o`，生成器不处理 `_OUTPUT_DIR`） | 否（读的是 v1 文档，且没把 `-o` 当确定性契约用） |

**两边都缺一份「结构化 I/O 契约」**：每个工具的脚本路径、入参 flag→数据类型、`-o` 输出目录、产物文件名（相对 `-o`）。v2 的 `-o` 正是这份契约的载体——它把产物路径从「脚本内部隐式知识」变成「接口上的显式约定」。

---

## 5. 改进方向（仅建议，未实施）

> 以下是分析推导出的修复方向，**本轮只写报告，不动代码**。

### 5.1 让两路都先「切到 v2」
- DB 的 `Script`/`ScriptCallDef` 从 `Amplicon_v2/reference` 重新 seed；
- `_AMPLICON_REF_DIR` 指向 `scripts/Amplicon_v2/reference`。

### 5.2 算法路：把 `-o` 接进数据流
- 给每个 `ScriptCallDef` 补 `-o` 参数（`data_type="_OUTPUT_DIR"`），并约定产物在 `<Tool>_Output/` 下；
- 在 `_build_single_command` 里**真正处理 `_OUTPUT_DIR`**：发 `-o "${TOOL}_OUT"`，并把 `produced[dt]` 记成**带目录前缀**的路径（`${DADA2_OUT}/featureSeqs.qza`），下一步 `-i` 直接引用；
- 顺手消掉两处 tool_id 地雷：per-sample 分发改成「按 `ScriptCallDef` 通用生成 body」（不再 `raise ValueError`）；DADA2 特判改成「检测 `_MANIFEST` 参数」通用化。
  > （这一项已有详细实施方案，见计划文件 `cuddly-inventing-frog.md`。）

### 5.3 LLM 路：喂契约，别喂散文
- `_load_tool_reference_md` 不要 `f.read()` 整篇；改成**抽取紧凑契约**：脚本路径、入参 flag 列表、`-o` 目录名、产物文件名清单。每工具压缩到几行；
- 删掉/弱化规则 4、15 的「防御性 rename」要求——有了 `-o`，产物名是确定性的，不需要兜底重命名；
- 加结构化约束：限定只输出「调用行 + 必要变量」，禁止大段行内注释；可考虑 `response_format` 让模型按「每步一条调用」结构化返回再拼脚本。

### 5.4 验证
- 用同一组 `tool_ids` + 上传文件，分别用 v1 / v2 各跑一次双路生成，`diff` 产物脚本，确认 v2 下两路都能正确串链（无 `<DATA_TYPE>` 占位、无防御性 rename、文件名能对上）。

---

## 附录：关键代码定位（`henry-dev`）

| 位置 | 说明 |
|---|---|
| `app/services/chat_service.py:1092` | 算法路调用 `generate_orchestrator_script` |
| `app/services/chat_service.py:1109` | LLM 路调用 `_generate_orchestrator_with_llm` |
| `app/services/chat_service.py:1129-1135` | `script1`/`script2`/`status`/`errors` 装载 |
| `app/services/chat_service.py:639` | `_load_tool_reference_md`（`f.read()` 整篇，啰嗦元凶） |
| `app/services/chat_service.py:664` | `_generate_orchestrator_with_llm`（15 条规则 prompt，temp 0.3） |
| `app/services/chat_service.py:751-754` | `_AMPLICON_REF_DIR` 写死指向 v1 |
| `app/services/chat_service.py:958` | 旧 `_generate_script_with_llm`（死代码，无调用方） |
| `pkg/amplicon/orchestrator.py:47` | `generate_orchestrator_script` 算法入口 |
| `pkg/amplicon/orchestrator.py:202` | 产物注册为裸文件名（无目录） |
| `pkg/amplicon/orchestrator.py:331-338` | per-sample 按 tool_id 分发 + `raise ValueError` 地雷 |
| `pkg/amplicon/orchestrator.py:374-376` | DADA2 产物 key 硬编码 |
| `pkg/amplicon/orchestrator.py:379-441` | `_build_single_command`，无 `_OUTPUT_DIR` 分支 |
| `pkg/amplicon/script_registry.py:39` | 全库唯一一处 `_OUTPUT_DIR`（仅 import-fasta） |
