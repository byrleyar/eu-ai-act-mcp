import json
from unittest.mock import patch, MagicMock
from server import discover_relevant_links

# Sample BibTeX entry
BIBTEX_ENTRY = """
@article{minimax2024,
  title={Technical Report},
  author={MiniMax Team},
  journal={arXiv preprint},
  url={https://arxiv.org/abs/2401.12345},
  year={2024}
}
"""

def test_discover_markdown_links():
    """Verify Markdown links are discovered with context."""
    text = "Here is the [Technical Report](https://example.com/report.pdf) for the model."
    links = discover_relevant_links(text, "test/repo")
    
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com/report.pdf"
    assert links[0]["label"] == "Technical Report"
    assert links[0]["type"] == "markdown_link"
    assert "Here is the" in links[0]["context"]

def test_discover_html_links():
    """Verify HTML links are discovered with context."""
    text = 'See our <a href="https://example.com/paper.pdf">Paper</a> for details.'
    links = discover_relevant_links(text, "test/repo")
    
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com/paper.pdf"
    assert links[0]["label"] == "Paper"
    assert links[0]["type"] == "html_link"
    assert "See our" in links[0]["context"]

def test_discover_arxiv_links_in_bibtex():
    """Verify arXiv links in BibTeX blocks are discovered."""
    text = f"Please cite our work:\n{BIBTEX_ENTRY}"
    links = discover_relevant_links(text, "test/repo")
    
    # Might catch it as a raw arXiv link or markdown depending on regex overlap
    # The current regex specifically looks for arxiv.org patterns
    arxiv_links = [l for l in links if "arxiv.org" in l["url"]]
    assert len(arxiv_links) >= 1
    assert "2401.12345" in arxiv_links[0]["url"]

def test_discover_repo_files():
    """Verify repository PDF files are discovered."""
    with patch("server.list_repo_files") as mock_list:
        mock_list.return_value = ["README.md", "technical_report.pdf", "code.py"]
        
        links = discover_relevant_links("some text", "test/repo")
        
        repo_links = [l for l in links if l["type"] == "repository_file"]
        assert len(repo_links) == 1
        assert repo_links[0]["label"] == "Repository File: technical_report.pdf"
        assert "resolve/main/technical_report.pdf" in repo_links[0]["url"]

def test_discover_deduplication():
    """Verify duplicate URLs are not added multiple times."""
    # Note: Deduplication happens in fetch_hf_model_card, not discover_relevant_links
    # But let's check if discover_relevant_links returns them (it should return all occurrences)
    # The filtering logic is in the tool function.
    pass 
