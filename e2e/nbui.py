"""Drive the NetBox web UI like a user, and read objects back through the REST API."""

import re


class NetBoxUI:
    def __init__(self, page):
        self.page = page

    # ---- generic UI ----------------------------------------------------

    def goto(self, path):
        self.page.goto(path)
        self.page.wait_for_load_state('networkidle')

    def click_header_button(self, text):
        """A button of the page header, e.g. Add or Import of a list page."""
        self.page.locator('.page-header a.btn, .page-header button.btn').filter(
            has_text=re.compile(rf'^\s*{re.escape(text)}\s*$')
        ).first.click()
        self.page.wait_for_load_state('networkidle')

    def select(self, name, option, search=None):
        """Choose an option of a NetBox select field (TomSelect)."""
        page = self.page
        wrapper = page.locator(f'select[name="{name}"] ~ .ts-wrapper').first
        for _attempt in range(4):
            if not page.locator('.ts-dropdown:visible').count():
                wrapper.locator('.ts-control').click()
                if search:
                    page.keyboard.type(search, delay=30)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(300)
            try:
                page.locator('.ts-dropdown .option:visible', has_text=option).first.click(timeout=5000)
                break
            except Exception:
                page.keyboard.press('Escape')
        else:
            raise AssertionError(f'Cannot choose {option!r} in the field {name}')
        page.wait_for_load_state('networkidle')
        if page.locator('.ts-dropdown:visible').count():
            page.keyboard.press('Escape')
        assert option in self.selected(name), (name, option, self.selected(name))

    def selected(self, name):
        """The text of the selected option of a select field ('' if none)."""
        texts = self.page.locator(f'select[name="{name}"] option:checked').all_inner_texts()
        return ' '.join(t.strip() for t in texts if t.strip() and not t.strip().startswith('-'))

    def submit(self):
        """Submit the form of the page and fail with its errors if it is shown again."""
        url = self.page.url
        self.page.locator('.page-body form button[type=submit]').filter(visible=True).first.click()
        self.page.wait_for_load_state('networkidle')
        errors = self.form_errors()
        assert not errors and self.page.url != url, f'The form was not accepted: {errors}'

    def form_errors(self):
        """Errors of a form: at its fields, and in Error toasts (e.g. of a bulk import)."""
        errors = [
            e.strip() for e in self.page.locator(
                '.page-body .invalid-feedback, .page-body .alert-danger, .page-body .errorlist'
            ).all_inner_texts() if e.strip()
        ]
        toasts = self.page.locator('.toast').filter(
            has=self.page.locator('.toast-header', has_text='Error')
        )
        errors += [' '.join(t.split()) for t in toasts.all_inner_texts()]
        return errors

    def import_yaml(self, list_path, data):
        """Click Import on a list page, paste YAML and submit (as the guide describes)."""
        self.goto(list_path)
        self.click_header_button('Import')
        self.page.fill('textarea[name="data"]', data)
        self.select('format', 'YAML')
        self.submit()

    # ---- REST API (with the session of the browser) ----------------------

    def api(self, path, **params):
        response = self.page.request.get(f'/api/{path.strip("/")}/', params=params)
        assert response.ok, f'GET /api/{path}: {response.status} {response.text()[:300]}'
        return response.json()

    def api_list(self, path, **params):
        return self.api(path, limit=1000, **params)['results']

    def api_one(self, path, **params):
        results = self.api_list(path, **params)
        assert len(results) == 1, f'{path} {params}: {len(results)} results'
        return results[0]

    def interface(self, device, name):
        return self.api_one('dcim/interfaces', device=device, name=name)

    def trace_far_ends(self, interface_id):
        """'<device> <interface>' of the far ends of the cable path of an interface."""
        segments = self.api(f'dcim/interfaces/{interface_id}/trace')
        if not segments:
            return []
        far = segments[-1][2]
        far = far if isinstance(far, list) else [far]
        return [f'{t["device"]["name"]} {t["name"]}' for t in far if t]

    def trace_page(self, device, name):
        """Open the interface page, click Trace and return the text of the trace page."""
        interface = self.interface(device, name)
        self.goto(f'/dcim/interfaces/{interface["id"]}/')
        self.page.locator(f'a[href*="/dcim/interfaces/{interface["id"]}/trace/"]').first.click()
        self.page.wait_for_load_state('networkidle')
        return ' '.join(self.page.locator('.page-body').inner_text().split())

    # ---- netbox-assets ----------------------------------------------------

    def create_asset(self, module_type, serial, name=None, asset_tag=None):
        """Assets → Assets → Add, with a module type; returns the URL of the asset page."""
        self.goto('/plugins/assets/assets/')
        self.click_header_button('Add')
        if name:
            self.page.fill('input[name="name"]', name)
        if asset_tag:
            self.page.fill('input[name="asset_tag"]', asset_tag)
        self.select('status', 'Stored')
        self.page.fill('input[name="serial"]', serial)
        self.page.click('a.nav-link[href="#module_type"]')
        self.select('module_type', module_type, search=module_type[:12])
        self.submit()
        assert '/plugins/assets/assets/' in self.page.url
        return self.page.url.split('?')[0]

    def ends_panel(self, asset_url):
        """The Assembly Ends panel: (cable summary, [(end, side, device, module bay)], warnings)."""
        self.goto(asset_url)
        panel = self.page.locator('#assembly-ends')
        # the cable line without the warnings below it
        summary = panel.locator('.card-body').first.evaluate(
            "e => { const c = e.cloneNode(true); c.querySelectorAll('.alert').forEach(a => a.remove());"
            " return c.textContent; }"
        )
        summary = ' '.join(summary.split())
        rows = []
        for row in panel.locator('tbody tr').all():
            cells = [' '.join(c.split()) for c in row.locator('td').all_inner_texts()]
            rows.append(tuple(cells[:4]))
        warnings = [' '.join(w.split()) for w in panel.locator('.alert-warning').all_inner_texts()]
        return summary, rows, warnings

    def asset_status(self, asset_url):
        self.goto(asset_url)
        return self.page.locator('.page-body tr', has_text='Status').locator('span.badge').first.inner_text().strip()

    def open_install(self, asset_url, end):
        self.goto(asset_url)
        self.page.locator('#assembly-ends tr').filter(has_text=end).locator(
            'a', has_text='Install'
        ).filter(visible=True).first.click()
        self.page.wait_for_load_state('networkidle')

    def install(self, asset_url, end, device, module_bay, preselected=None, module_type=None):
        """
        Click Install next to an end, choose the device and module bay, and create.

        preselected: the module type the form must preselect ('' for none, None: no check)
        module_type: a module type to choose in the form
        """
        self.open_install(asset_url, end)
        assert end in self.selected('label'), f'End {end} is not preselected'
        self.select('device', device, search=device)
        self.select('module_bay', module_bay)
        if preselected is not None:
            current = self.selected('module_type')
            if preselected:
                assert preselected in current, f'{end}: module type {current!r} preselected, not {preselected}'
            else:
                assert current == '', f'{end}: module type {current!r} preselected, expected none'
        if module_type:
            self.select('module_type', module_type, search=module_type[:12])
        self.submit()

    def uninstall(self, asset_url, end):
        """Click Uninstall next to an end and confirm."""
        self.goto(asset_url)
        self.page.locator('#assembly-ends tr').filter(has_text=end).locator(
            'a', has_text='Uninstall'
        ).filter(visible=True).first.click()
        self.page.wait_for_load_state('networkidle')
        self.page.locator('.page-body form button[type=submit]').filter(visible=True).first.click()
        self.page.wait_for_load_state('networkidle')
