import re
import hashlib

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor


def makeExtension(configs=None):
    if configs is None:
        return ChecklistsExtension()
    else:
        return ChecklistsExtension(configs=configs)


class ChecklistsExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        md.postprocessors.add('checklists', ChecklistsPostprocessor(md),
                              '>raw_html')


class ChecklistsPostprocessor(Postprocessor):
    """
    adds checklists class to list element
    """

    pattern = re.compile(r'<li>\[([ Xx])\](.*)</li>')
    nested = re.compile(r'<li>\[([ xX])\](.*<ul.*>(\n<li.*)+)<\/li>')
    # @see `item_pattern` on regex101.com: https://regex101.com/r/lH6fL1/1
    item_pattern = re.compile(
        r'(<li.*<input type="checkbox"([ ]?id="[^"]*"))( checked)?(>)([\s\S]*?)(</li>)')
    item_nested = re.compile(
        r'(<li.*<input type="checkbox"([ ]?id="[^"]*"))( checked)?(>)([\s\S]*?)(<ul)')

    def run(self, html):
        html = re.sub(self.pattern, self._convert_checkbox, html)
        before = '<ul>\n<li class="task-list-item"><input type="checkbox"'
        after = before.replace('<ul>', '<ul class="checklist">')
        checked_html = html.replace(before, after)
        checked_labeld_html = re.sub(
            self.item_pattern, self._convert_label, checked_html)
        html = re.sub(self.nested, self._convert_checkbox, checked_labeld_html)
        checked_html = html.replace(before, after)
        checked_labeld_html = re.sub(
            self.item_nested, self._convert_label, checked_html)
        return checked_labeld_html

    def _convert_checkbox(self, match):
        state = match.group(1)
        item = match.group(2)
        checked = ' checked' if state != ' ' else ''
        attrib_id = ' id="%s"' % self._create_item_id(
            item) if (item != ' ') and (item != '') else ''
        return'<li class="task-list-item"><input type="checkbox"%s%s>%s</li>' % (attrib_id, checked, item)

    def _convert_label(self, match):
        # <li class=""><input type="checkbox" id="" checked>
        before_item = match.group(1)
        inside_input_id = match.group(2)  # id=""
        inside_input_checked = match.group(3)  # checked
        item = match.group(5)  # baz
        after_item = match.group(6)  # </li>
        attrib_for = ' for="%s"' % self._create_item_id(
            item) if (item != ' ') and (item != '') else ''
        if inside_input_checked is not None:
            return '%s checked disabled><label%s>%s</label>%s' % (before_item, attrib_for, item, after_item)
        else:
            return '%s disabled><label%s>%s</label>%s' % (before_item, attrib_for, item, after_item)

    def _create_item_id(self, item):
        return hashlib.sha256(item.encode()).hexdigest()
