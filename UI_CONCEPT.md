# UI Concept: User Interaction Flows

This document conceptually describes how a user might interact with the automated press release system, outlining user flows and key interaction points at a high level.

## 1. Dashboard/Project Overview

*   **Initial View:** Upon logging in, the user is greeted with a personalized Dashboard.
    *   **Main Area:** Displays a list or card view of their existing "Press Release Projects." Each entry would show:
        *   Project Name
        *   Current Status (e.g., "Draft," "Generating Content," "Pending Review," "Distributing," "Completed," "Archived").
        *   Key date (e.g., Last Modified, Creation Date, or Scheduled Distribution Date).
        *   Quick summary metrics if available (e.g., number of contacts targeted, open rate for completed campaigns).
    *   **Primary Action:** A prominent "Create New Project" button.
    *   **Navigation:** A sidebar or top navigation bar providing access to:
        *   Projects (the dashboard itself)
        *   Global Contact Lists (if they can manage these separately)
        *   Global Publication Lists (if applicable)
        *   Templates (for press releases or projects)
        *   Analytics/Reports (overall campaign performance)
        *   User Account/Settings.
    *   **Search/Filtering:** Options to search for projects by name or filter by status.

## 2. Project Creation & Setup

This flow is initiated by clicking the "Create New Project" button.

*   **Step 1: Basic Project Information**
    *   **Input Fields:**
        *   `Project Name/Title:` (e.g., "Q3 Product Launch," "New Partnership Announcement").
        *   `Company/Client Details:` (If the user manages multiple entities, this might be a dropdown or a section to input company name, boilerplate, website, media contact person for this specific release). This could also pull from pre-saved company profiles.
    *   **Action:** "Next" or "Save and Continue to Content."

*   **Step 2: Core Message & Content Inputs**
    *   **Input Fields:**
        *   `Key Message/Announcement:` A concise summary of the core news (e.g., "We are launching Product X on Date Y," "Company A is partnering with Company B.").
        *   `Main Talking Points/Details:` Bullet points or a text area for users to list essential information, facts, figures, and benefits to be included in the press release.
        *   `Quotes:` Dedicated fields to input quotes and attribute them (e.g., "Quote 1 Text," "Quote 1 Attributed To," "Quote 1 Title"). Option to add multiple quotes.
        *   `Call to Action:` What should readers do after reading the press release? (e.g., visit a website, register for an event).
    *   **File Uploads (Optional):**
        *   `Supporting Documents:` For background information, fact sheets.
        *   `Company Logo/Media Assets:` To be included with the release if the format supports it.
    *   **Action:** "Next" or "Save and Continue to Audience."

*   **Step 3: Defining Goals & Target Audience**
    *   **Goals of the Press Release (Checkboxes/Dropdown):**
        *   `Increase Brand Awareness`
        *   `Announce New Product/Service`
        *   `Drive Website Traffic`
        *   `Generate Media Pick-up`
        *   `Crisis Communication`
        *   `Partnership Announcement`
        *   (User could select multiple or specify 'Other').
    *   **Target Audience Description (Keywords/Text Area):**
        *   `Industry Keywords:` (e.g., "fintech," "renewable energy," "healthcare IT").
        *   `Geographic Focus:` (e.g., "Global," "North America," "Specific Cities/Regions" - could be a map interface or text input).
        *   `Publication Types:` (e.g., "Tech Blogs," "National Newspapers," "Trade Magazines," "Local News").
        *   `Audience Interests/Demographics (Optional):` Free-text description of the desired reader.
    *   **Action:** "Save Project" or "Finish Setup & Go to Project Dashboard." The project is now created and likely moves to a "Draft" status. The user might be navigated to the project's specific dashboard/workspace.

## 3. Press Release Generation & Refinement

This section is typically accessed from an individual project's workspace/dashboard after the initial setup.

*   **Triggering Generation:**
    *   A clear "Generate Press Release" button would be visible if content hasn't been generated yet or if the user wishes to regenerate.
    *   **Options before generation (Modal/Dropdown):**
        *   `Select Template:` User could choose from pre-defined templates (e.g., "New Product Launch," "Event Announcement," "Partnership News") or their own custom templates.
        *   `Select Tone/Style (Optional):` Dropdown with options like "Formal," "Informal," "Excited," "Neutral."
        *   `Target Length (Optional):` Options like "Short (~300 words)," "Medium (~500 words)," "Long (~800 words)."
    *   Upon clicking "Generate," a progress indicator would appear (e.g., "AI is drafting your press release...").

*   **Reviewing and Editing:**
    *   **Editor Interface:** The generated draft appears in a rich-text editor (like TinyMCE, CKEditor, or a custom one).
        *   Standard formatting tools (bold, italics, lists, headings, links).
        *   **AI Suggestions/Prompts:**
            *   Inline suggestions for rephrasing sentences or paragraphs (e.g., different wording options on hover/click).
            *   "Improve Clarity," "Make More Concise," "Suggest Alternative Headline" buttons for selected text sections or the whole document.
            *   A sidebar could offer AI-generated keywords, a summary, or a sentiment analysis of the draft.
            *   Prompts to add specific information if the AI detects missing elements based on the project goals or common press release structures (e.g., "Consider adding a quote here," "Is there a specific call to action you'd like to include?").
    *   **Real-time Feedback:** Readability scores (e.g., Flesch-Kincaid), grammar/spell check highlights.

*   **Version Control & Templates:**
    *   **Version History:** A simple versioning system (e.g., "Version 1 - AI Draft," "Version 2 - User Edits"). User can view and potentially revert to previous versions.
    *   **Saving Changes:** "Save Draft" button.
    *   **Save as Template:** Option to save the current edited version (or a previous version) as a new custom template for future use.
    *   **Loading Templates:** Ability to load a different template onto the current content, which might overwrite or attempt to merge, with user confirmation.

*   **Action:** "Save and Continue to Audience Targeting" or similar button to proceed to the next stage. "Mark as Final Draft" option.

## 4. Audience Targeting & Contact List Management

This stage follows press release finalization, or can be worked on in parallel if the inputs are ready.

*   **Input for Publication/Contact Identification:**
    *   This section would re-display or allow modification of the `Industry Keywords`, `Geographic Focus`, and `Publication Types` defined during Project Setup.
    *   **Additional Filters (Optional):**
        *   `Publication Reach/Circulation (Slider/Dropdown):` e.g., "Local," "Regional," "National," "International."
        *   `Media Type (Checkboxes):` e.g., "Online," "Print," "Radio," "TV."
        *   `Exclude specific publications/contacts:` A field to list any known entities to avoid.
    *   **Action:** "Find Publications & Contacts" button. A progress indicator would show while the system searches.

*   **Reviewing Suggested Publications & Contacts:**
    *   **Display Format:** A list or card view of suggested publications and, nested within or separately, the contacts associated with them.
        *   **Publication Card/Row:** Publication Name, Website, Brief Description, Relevance Score (how well it matches criteria), Type (e.g., Blog, Newspaper), Reach (if available).
        *   **Contact Card/Row:** Contact Name, Job Title, Associated Publication, Email (partially masked or available), Relevance Score (if applicable, e.g., based on beat), quick link to their articles or profile.
    *   **Filtering & Sorting:**
        *   Filter by publication type, relevance score, location.
        *   Sort by name, relevance, reach.
    *   **Selection Tools:**
        *   Checkboxes next to each publication/contact to select them for the outreach list.
        *   "Select All," "Deselect All" options.
        *   "Approve" (add to project's target list) or "Reject" (remove from suggestions, potentially add to a project-specific exclusion list or global "do not contact" list) buttons for individual or bulk selections.
        *   A "View Details" link for each publication/contact could open a modal or sidebar with more information (e.g., recent articles by the journalist, more detailed publication profile).

*   **Managing Contact Lists:**
    *   **Project-Specific List:** The selected contacts form a "Target List" for the current project. Users can view this list, remove contacts, or manually add new contacts (e.g., "Add Contact" button with fields for name, email, publication, etc.).
    *   **Uploading Custom Lists:**
        *   "Upload Contact List" button.
        *   Supports CSV/Excel file uploads.
        *   A mapping step where the user matches columns in their file (e.g., "FirstName," "EmailAddress") to system fields.
        *   Option to add uploaded contacts to the current project's target list or a global contact list.
    *   **Global Lists (if supported):** A separate section in the main navigation to manage master lists of contacts or publications that can be reused across projects.

*   **Action:** "Save Audience List" or "Proceed to Review & Distribute."

## 5. Review, Approval, and Distribution

This is the final checkpoint before the press release goes out.

*   **Consolidated Review Screen:**
    *   A single screen showing:
        *   **Final Press Release Preview:** A read-only view of the finalized press release content, exactly as it will be sent/formatted.
        *   **Selected Contact List Summary:** Key statistics about the list (e.g., "Total Contacts: 150," "Publications Targeted: 80"). A link to view the full list in a modal or separate tab.
        *   **Distribution Settings Preview:** Sender email address (e.g., `press@yourcompany.com` - may be configurable in settings), selected outreach method.
    *   **"Send Test Email" option:** Allows the user to send a preview of the email to their own address or a specified test address.

*   **Approval Step (Optional, depending on user roles/workflow):**
    *   If the system supports multi-user workflows (e.g., manager approval), there might be an "Submit for Approval" button.
    *   Approved/Rejected status would be visible.

*   **Distribution Options:**
    *   **Outreach Method Selection (if multiple are supported):**
        *   `Email Distribution:` (Likely the primary method).
            *   **Personalization Preview (Optional):** A way to see how a few sample emails will look with placeholders (e.g., `[Journalist Name]`, `[Publication Name]`) filled in.
        *   `Download for Manual Distribution:` Option to download the press release (e.g., DOCX, PDF) and the contact list (e.g., CSV, XLSX) for users who want to send it out manually or through a different system.
        *   `Newswire Integration (if supported):` Options to select and send to integrated newswire services. This would likely involve additional API authentications and cost considerations displayed to the user.
    *   **Scheduling:**
        *   `Send Now:` Initiates distribution immediately.
        *   `Schedule for Later:` User selects a date and time for distribution. A calendar/time picker interface. Option to select timezone.
    *   **Final Confirmation:** A prominent "Confirm & Distribute" or "Confirm & Schedule" button. A final warning/confirmation dialog (e.g., "You are about to send this press release to 150 contacts. Are you sure?").

*   **Post-Distribution Indication:**
    *   Once initiated, the project status updates to "Distributing" or "Scheduled."
    *   A brief confirmation message (e.g., "Your press release is being distributed," or "Your press release has been scheduled for [Date] at [Time].").

## 6. Campaign Monitoring & Reporting

This section is accessed from the individual project's workspace or a global "Analytics/Reports" section.

*   **Campaign Status View (within a Project):**
    *   After distribution, the project workspace would display a summary of the campaign.
    *   **Overall Metrics:**
        *   `Total Sent:` Number of emails successfully sent.
        *   `Total Delivered:` Number of emails successfully delivered.
        *   `Bounce Rate:` Percentage of emails that bounced.
        *   `Open Rate (if email tracking is enabled):` Percentage of delivered emails that were opened.
        *   `Click-Through Rate (if links are tracked):` Percentage of opened emails where a link was clicked.
    *   These could be displayed as numerical stats and potentially simple charts (e.g., a pie chart for delivery status).

*   **Detailed Recipient List View:**
    *   A table or list of all targeted contacts for that specific campaign.
    *   Columns for:
        *   `Contact Name`
        *   `Email Address`
        *   `Publication`
        *   `Delivery Status:` (e.g., "Sent," "Delivered," "Bounced - Hard," "Bounced - Soft," "Opened," "Clicked").
        *   `Timestamp` of last status update.
    *   **Filtering/Sorting:** Ability to filter by status (e.g., show all bounced emails), sort by publication, etc.
    *   **Error Details:** For bounced emails, if the system captures it, a reason for the bounce might be visible on hover or in a detail view.

*   **Global Analytics/Reports Page (Main Navigation):**
    *   **Overview:** Comparison of performance across multiple campaigns.
        *   Average open rates, click rates, bounce rates.
        *   Most successful campaigns (e.g., by open rate or number of clicks).
        *   Trends over time (e.g., chart showing open rates month over month).
    *   **Publication Performance (Aggregated):**
        *   Which publications or types of publications tend to have higher engagement (if trackable).
    *   **Contact Performance (Aggregated):**
        *   Which specific contacts are most engaged over time.
    *   **Customizable Reports:**
        *   Ability to filter reports by date range, specific projects, or target audience tags.
        *   Option to "Export Report" (e.g., to CSV or PDF) for key metrics or lists.

*   **User Interaction:**
    *   Clicking on a campaign in the dashboard could lead directly to its specific monitoring view.
    *   Visual cues (colors, icons) to quickly indicate campaign health or issues (e.g., high bounce rate).
    *   Links to "View Press Release" or "View Contact List" for context.
