"""
Custom template loader that fixes broken Django template tags.

This loader wraps the default Django template loader and fixes template tags
that have been split across multiple lines by auto-formatters.
"""
from django.template.loaders.filesystem import Loader as FilesystemLoader
import re


class FixedTemplateLoader(FilesystemLoader):
    """
    Template loader that fixes broken template tags before processing.
    
    Auto-formatters (like Prettier) often split Django template tags across
    multiple lines, which breaks the template parser. This loader fixes those
    tags by joining them back onto single lines.
    """
    
    def get_contents(self, origin):
        """Get template contents and fix broken tags."""
        contents = super().get_contents(origin)
        
        # Fix template tags split across lines
        # Pattern: {% ... \n ... %}
        contents = re.sub(
            r'{%\s*([^}]*?)\s*\n\s*([^}]*?)\s*%}',
            r'{% \1 \2 %}',
            contents,
            flags=re.MULTILINE
        )
        
        # Fix variable tags split across lines
        # Pattern: {{ ... \n ... }}
        contents = re.sub(
            r'{{\s*([^}]*?)\s*\n\s*([^}]*?)\s*}}',
            r'{{ \1 \2 }}',
            contents,
            flags=re.MULTILINE
        )
        
        return contents
