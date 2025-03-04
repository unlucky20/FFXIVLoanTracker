import requests
from bs4 import BeautifulSoup
import time

class LodestoneScraper:
    def __init__(self, fc_id="9228157111459014466"):
        self.fc_id = fc_id
        self.base_url = f"https://na.finalfantasyxiv.com/lodestone/freecompany/{fc_id}/member/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def get_all_members(self):
        """Scrapes all FC members from Lodestone, handling pagination dynamically."""
        members = []
        page = 1
        max_retries = 3

        while True:
            url = f"{self.base_url}?page={page}"
            print(f"📃 Fetching page {page}: {url}")

            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(2)  # Delay between retries

                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Updated selector for member entries
                    member_list = soup.select("div.entry__block")

                    if not member_list:
                        # Try alternative selector
                        member_list = soup.select("div.entry__freecompany__fc-member")

                    if not member_list:
                        print(f"❌ No members found on page {page}, trying different selector")
                        member_list = soup.select("li.entry")

                    if not member_list:
                        print("❌ Could not find member elements with any selector")
                        print("HTML preview:", soup.prettify()[:500])
                        return list(dict.fromkeys(members))  # Return unique members

                    # Process members on this page
                    for member_entry in member_list:
                        # Try different possible name element selectors
                        name_element = (
                            member_entry.select_one("p.entry__name") or
                            member_entry.select_one("div.entry__freecompany__fc-member__name") or
                            member_entry.select_one("p.entry__freecompany__member__name")
                        )

                        if name_element:
                            member_name = name_element.get_text(strip=True)
                            if member_name:
                                full_name = f"{member_name}\nBrynhildr"
                                if full_name not in members:  # Only add if not already in list
                                    members.append(full_name)

                    print(f"✅ Found {len(member_list)} members on page {page}")

                    # Check for next page button
                    next_button = soup.select_one("a.btn__pager__next")
                    if not next_button:
                        print("🏁 Reached last page")
                        return list(dict.fromkeys(members))  # Return unique members

                    # Success - move to next page
                    page += 1
                    break

                except requests.RequestException as e:
                    print(f"❌ Error fetching page {page} (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:  # Last attempt failed
                        return list(dict.fromkeys(members))  # Return unique members
                    time.sleep(2)  # Wait before retry

            # Safety check - don't go beyond reasonable number of pages
            if page > 10:  # Assuming FC won't have more than 10 pages of members
                print("🛑 Reached maximum page limit")
                break

        # Return unique members, preserving order
        return list(dict.fromkeys(members))