import urllib.request

url = 'https://raw.githubusercontent.com/jamalmazrui/extCheck/main/extCheck.cs'
with urllib.request.urlopen(url) as r:
    src = r.read().decode('utf-8')

print('Downloaded', len(src), 'bytes')

# Change 1: Add bYamlOpened field next to iYamlEndLine
old1 = '    static int iYamlEndLine;\n    static Regex reFence'
new1 = '    static int iYamlEndLine;\n    static bool bYamlOpened;\n    static Regex reFence'
assert old1 in src, 'Change 1 target not found'
src = src.replace(old1, new1, 1)
print('Change 1 OK: added bYamlOpened field')

# Change 2: Set bYamlOpened in parseYaml()
old2 = ('    static void parseYaml() {\n'
        '        if (aLines.Length < 2 || aLines[0].Trim() != "---") {\n'
        '            return;\n'
        '        }\n'
        '        for (int i = 1; i < aLines.Length; i++) {')
new2 = ('    static void parseYaml() {\n'
        '        bYamlOpened = false;\n'
        '        if (aLines.Length < 2 || aLines[0].Trim() != "---") {\n'
        '            return;\n'
        '        }\n'
        '        bYamlOpened = true;\n'
        '        for (int i = 1; i < aLines.Length; i++) {')
assert old2 in src, 'Change 2 target not found'
src = src.replace(old2, new2, 1)
print('Change 2 OK: parseYaml() tracks bYamlOpened')

# Change 3: Split the iYamlEndLine==0 check in metadata()
old3 = ('        if (iYamlEndLine == 0) {\n'
        '            add("NoYamlFrontMatter", 1, "MSAC", "Missing document properties", sFilePath,\n'
        '                "The file has no YAML front matter block. Without front matter, Pandoc cannot set document title, language, or author.",\n'
        '                "Add a YAML front matter block at the very top starting and ending with ---. Include at minimum: title and lang.");\n'
        '            return;\n'
        '        }')
new3 = ('        if (!bYamlOpened) {\n'
        '            add("NoYamlFrontMatter", 1, "MSAC", "Missing document properties", sFilePath,\n'
        '                "The file has no YAML front matter block. Without front matter, Pandoc cannot set document title, language, or author.",\n'
        '                "Add a YAML front matter block at the very top starting and ending with ---. Include at minimum: title and lang.");\n'
        '            return;\n'
        '        }\n'
        '        if (iYamlEndLine == 0) {\n'
        '            add("YamlFrontMatterUnclosed", 1, "MSAC", "Missing document properties", sFilePath,\n'
        '                "The YAML front matter block starting with --- on line 1 has no closing --- or ... delimiter. Pandoc will not process it as front matter.",\n'
        '                "Add a closing --- or ... line immediately after the last YAML field, before the document body begins.");\n'
        '            return;\n'
        '        }')
assert old3 in src, 'Change 3 target not found'
src = src.replace(old3, new3, 1)
print('Change 3 OK: metadata() distinguishes no-fence from unclosed-fence')

# Change 4: Add YamlFrontMatterUnclosed row to writeRulesCsv after NoYamlFrontMatter row
marker = '            new[] { "NoYamlFrontMatter","Missing document properties","2.4.2","Error","MD"'
assert marker in src, 'Change 4 marker not found'
idx = src.find(marker)
row_end = src.find('},', idx) + 2
insert_row = ('\n'
              '            new[] { "YamlFrontMatterUnclosed","Missing document properties","2.4.2","Error","MD",'
              '"The YAML front matter block starting with --- on line 1 has no closing --- or ... delimiter. Pandoc will not process it as front matter.",'
              '"Add a closing --- or ... line immediately after the last YAML field, before the document body begins." },')
src = src[:row_end] + insert_row + src[row_end:]
print('Change 4 OK: YamlFrontMatterUnclosed added to writeRulesCsv()')

print('All 4 changes applied. New size:', len(src), 'bytes')

with open('tmp/extCheck_modified.cs', 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print('Saved to tmp/extCheck_modified.cs')
