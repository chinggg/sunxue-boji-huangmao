# 贡献指南

欢迎补充。这个仓库的价值不在它多完整，而在它**能不能被别人改得更好**。

## 三种最受欢迎的贡献

### 1. 补一手材料 ⭐ 最缺

这套理论散落在播客、社交媒体发帖和评论里。如果你有：

- 孙宇晨 / 邵艾伦关于孙学、薄肌、黄毛的**原始发言截图或链接**
- 更早的出处的考据
- 访谈的其他整理版本

开个 issue 或直接 PR 到 `docs/`，并在文末标注来源。

### 2. 加可执行的东西

理论文档我们已经够多了，缺的是**能跑的东西**：

- `scripts/sunxue.py` 的新子命令（必须保持零第三方依赖）
- `prompts/` 下新的、经过实测的 Prompt
- `templates/` 下更好用的记录模板

要求：**你自己先真的用过一次**。PR 里说明你在什么场景下用的、效果如何。

### 3. 反驳

最欢迎的一类 PR：**你不同意某个论断**。

`docs/09-边界-争议与反面.md` 是专门留给批评意见的。
如果你能给出更锋利的反驳，或者直接指出文档里的逻辑漏洞，开 PR。
**我们更怕这套东西变成自洽的闭环，而不是怕它被打穿。**

## 规范

- 文档用简体中文，代码块与命令保持原样
- `scripts/sunxue.py` 必须兼容 Python 3.8+，不引入任何第三方依赖
- 新增 SVG 图放在 `assets/`，必须能通过 XML 解析检查
- 引用他人观点要标注来源

## 自检

提交前跑一遍：

```bash
# 1. CLI 冒烟
python3 scripts/sunxue.py --answers "4,4,4,4,4,4,4,4,4" diag
python3 scripts/sunxue.py --answers "75,29,172,15" body
python3 scripts/sunxue.py --answers "100,10" 37
python3 scripts/sunxue.py quote

# 2. SVG 合法性
python3 -c "
import xml.etree.ElementTree as ET, glob
for f in glob.glob('assets/*.svg'): ET.parse(f); print('ok', f)
"
```

## 边界

- 不接受投资建议类内容
- 不接受医疗建议类内容
- 不接受人身攻击

## License

贡献即视为同意以 MIT 许可发布。
