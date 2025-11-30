from playwright.sync_api import sync_playwright
import time

def verify_colors():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 3000})

        try:
            page.goto("http://localhost:8080")

            # Remove fade-in-up class entirely to disable animation logic
            page.evaluate("""() => {
                document.querySelectorAll('.fade-in-up').forEach(el => {
                    el.classList.remove('fade-in-up');
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                    el.style.visibility = 'visible';
                });
            }""")

            page.wait_for_timeout(1000)

            # Screenshot of the top part (Hero)
            page.screenshot(path="hero_section.png", clip={"x": 0, "y": 0, "width": 1280, "height": 1000})
            print("Captured hero_section.png")

            # Scroll down
            page.evaluate("window.scrollTo(0, 1000)")
            page.wait_for_timeout(500)
            page.screenshot(path="what_i_do_section.png", clip={"x": 0, "y": 1000, "width": 1280, "height": 1000})
            print("Captured what_i_do_section.png")

            # Footer
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)
            page.screenshot(path="footer_section.png", full_page=True)
            print("Captured footer_section.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_colors()
