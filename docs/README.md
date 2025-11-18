# RobAI Tools Documentation

This directory contains the documentation for RobAI Tools, built with Jekyll and the Just the Docs theme.

## Local Development

### Prerequisites

- Ruby 3.2 or higher
- Bundler gem

### Setup

1. Install dependencies:
   ```bash
   cd docs
   bundle install
   ```

2. Run the local server:
   ```bash
   bundle exec jekyll serve
   ```

3. Open your browser to `http://localhost:4000/robaitools/`

### Live Reloading

The Jekyll server will automatically rebuild the site when you make changes to files. Just refresh your browser to see updates.

## Project Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── Gemfile                  # Ruby dependencies
├── index.md                 # Landing page
├── .gitignore               # Jekyll build artifacts
└── <project-name>/          # Each project has its own directory
    ├── index.md             # Project overview (parent page)
    ├── getting-started.md   # Installation & setup
    ├── configuration.md     # Configuration options
    ├── api-reference.md     # API endpoints/usage
    └── architecture.md      # Design & architecture
```

## Writing Documentation

### Front Matter

Each markdown file must start with YAML front matter:

```yaml
---
layout: default
title: Page Title
parent: project-name    # For child pages
nav_order: 1            # Optional: controls order in navigation
---
```

### Navigation Hierarchy

- **Parent pages** (project index): Set `has_children: true`
- **Child pages**: Set `parent: project-name`
- Use `nav_order` to control the order of items in the navigation

### Callouts

Just the Docs supports callouts for important information:

```markdown
{: .note }
This is a note callout.

{: .warning }
This is a warning callout.

{: .important }
This is an important callout.
```

### Code Blocks

Use fenced code blocks with syntax highlighting:

````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

### Links

- Internal links: `[Link Text](../other-page.md)`
- External links: `[Link Text](https://example.com)`

## GitHub Pages Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

### Initial Setup

1. Go to your GitHub repository settings
2. Navigate to **Pages** section
3. Under **Source**, select **GitHub Actions**
4. The workflow in `.github/workflows/pages.yml` will handle the rest

### Viewing the Published Site

Once deployed, the site will be available at:
`https://rob-p-smith.github.io/robaitools/`

## Adding New Projects

To add a new project to the documentation:

1. Create a new directory: `docs/new-project/`
2. Create an index page with `has_children: true`
3. Add child pages with `parent: new-project`
4. Update the main `index.md` to link to the new project

## Theme Customization

The site uses the Just the Docs theme. For advanced customization options, see:
https://just-the-docs.github.io/just-the-docs/

## Support

For issues with the documentation site:
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Just the Docs Documentation](https://just-the-docs.github.io/just-the-docs/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
