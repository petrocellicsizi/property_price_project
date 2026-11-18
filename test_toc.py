import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = docx.Document()
p_begin = doc.add_paragraph()
fld_begin = parse_xml(f'<w:r {nsdecls(" w\)}><w:fldChar w:fldCharType=\begin\/><w:instrText xml:space=\preserve\> TOC \\o \1-3\ \\h \\z \\u </w:instrText><w:fldChar w:fldCharType=\separate\/></w:r>')
p_begin._p.append(fld_begin)

p_item = doc.add_paragraph()
p_item.text = '1.\tBevezetés\t7'

p_end = doc.add_paragraph()
fld_end = parse_xml(f'<w:r {nsdecls(\w\)}><w:fldChar w:fldCharType=\end\/></w:r>')
p_end._p.append(fld_end)

doc.save('test_toc.docx')
print('test_toc.docx saved successfully')
