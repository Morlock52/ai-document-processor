# UI Mockup Guide

## Overview

The AI Document Processor features a modern, user-friendly interface built with React/Next.js and styled with Tailwind CSS. This guide showcases the design and user experience.

## Viewing the Mockup

### Quick View
Simply open `UI_MOCKUP.html` in any modern web browser:

```bash
# From project root
open UI_MOCKUP.html

# Or on Linux
xdg-open UI_MOCKUP.html

# Or on Windows
start UI_MOCKUP.html
```

**No server required!** The mockup is a standalone HTML file with all styles and JavaScript embedded.

---

## Interface Components

### 1. Hero Section
![Hero Section](images/hero-section.png)

**Features:**
- **Eye-catching gradient** background (blue → indigo → purple)
- **AI-Powered badge** to highlight the technology
- **Large headline** with gradient text effect
- **Two CTA buttons**: "Get Started" (primary) and "View Demo" (secondary)
- **Grid pattern overlay** for visual depth

**User Journey:**
- First impression: "This is an AI-powered tool"
- Call to action: Clear next steps

---

### 2. Template Mode Toggle
![Template Mode](images/template-mode.png)

**Functionality:**
- **Toggle button** to enable/disable template mode
- **Visual feedback**:
  - Disabled: Gray background
  - Enabled: Emerald green background with expanded info panel
- **Info panel** explains template mode benefits:
  - All fields become Excel columns
  - Each document becomes a row
  - Consolidated export

**Use Cases:**
- **Individual mode** (default): Process each document separately
- **Template mode** (toggled): Create unified Excel with all documents

---

### 3. Upload Tab

#### 3a. Drag & Drop Zone
![Dropzone](images/dropzone.png)

**Features:**
- **Large drop area** with clear visual hierarchy
- **Upload icon** with gradient background and glow effect
- **Interactive states**:
  - Default: Gentle hover effect
  - Active drag: Scale up, change background
  - Hover: Shadow and background transition
- **File requirements** clearly displayed:
  - PDF files only
  - Max 100MB each
  - Batch upload supported

**User Experience:**
- Obvious drop target
- Clear constraints
- Encouraging messaging

#### 3b. Upload Progress
![Upload Progress](images/upload-progress.png)

**Components:**
- **Progress header** with icon and divider
- **File cards** showing:
  - Filename with truncation
  - File size
  - Status (Uploading, Complete, Failed)
  - Progress bar (for active uploads)
  - Action buttons (Remove, Retry)

**Status Indicators:**
1. **Uploading** (Blue)
   - Animated pulse icon
   - Progress percentage
   - Animated progress bar

2. **Success** (Green)
   - Checkmark icon
   - "Upload Complete" message
   - No progress bar

3. **Error** (Red)
   - Alert icon
   - Error message in expandable panel
   - Retry button (if retryable)

#### 3c. How It Works Section
![How It Works](images/how-it-works.png)

**3-Step Process:**

**Step 1: Upload PDFs**
- Blue gradient icon (document)
- Numbered badge (1)
- Description of drag-and-drop functionality

**Step 2: AI Processing**
- Purple gradient icon (lightning bolt)
- Numbered badge (2)
- GPT-4o Vision mention

**Step 3: Export to Excel**
- Green gradient icon (download)
- Numbered badge (3)
- Formatted spreadsheets promise

**Design Pattern:**
- Consistent icon sizing (64px)
- Gradient backgrounds matching brand
- Hover effects (scale + shadow)
- Clear typography hierarchy

---

### 4. Documents Tab

#### 4a. Document Library Header
![Library Header](images/library-header.png)

**Elements:**
- **Library icon** with gradient background
- **Document count** and **status summary**
- **Action buttons**:
  - "Download Selected (X)" - Primary action (emerald green)
  - "Refresh" - Secondary action (outline)
- **Select all checkbox** for bulk operations

#### 4b. Document Cards
![Document Cards](images/document-cards.png)

**Card Components:**

**Layout:**
- Checkbox (left)
- Document icon (gradient background)
- Document details (center, flexible)
- Action buttons (right, hidden on default, visible on hover)

**Document Details:**
1. **Filename** (bold, truncated if long)
2. **Status badge** with icon:
   - Pending (yellow with clock icon)
   - Processing (blue with spinner - animated)
   - Completed (green with checkmark)
   - Failed (red with X icon)
3. **Progress bar** (only for "Processing" status)
4. **Metadata**:
   - Page count with document icon
   - Upload date/time with calendar icon

**Actions (on hover):**
- **Download** button (emerald) - Only for completed docs
- **Delete** button (red) - Available for all

**Interactive States:**
```css
Default    → Clean, minimal
Hover      → Shadow appears, actions visible
Selected   → Checkbox checked, included in bulk ops
Processing → Animated spinner, progress bar
```

---

## Color Scheme

### Primary Colors
```css
Indigo/Purple Gradient:
- from-indigo-600 to-purple-600
- Used for: Primary CTAs, hero elements

Blue Gradient:
- from-blue-500 to-indigo-600
- Used for: Icons, upload zone

Emerald/Teal Gradient:
- from-emerald-500 to-teal-600
- Used for: Success states, template mode
```

### Status Colors
```css
Pending:    Yellow  (#EAB308) - Waiting
Processing: Blue    (#3B82F6) - Active
Completed:  Green   (#10B981) - Success
Failed:     Red     (#EF4444) - Error
```

### Neutral Colors
```css
Gray 50:  #F9FAFB - Background
Gray 100: #F3F4F6 - Subtle backgrounds
Gray 600: #4B5563 - Secondary text
Gray 900: #111827 - Primary text
```

---

## Interactive Elements

### Buttons

**Primary (Gradient)**
```html
<button class="bg-gradient-to-r from-indigo-600 to-purple-600
               hover:from-indigo-700 hover:to-purple-700
               rounded-2xl shadow-lg hover:shadow-xl">
```
- Used for: Main actions
- States: Default, Hover, Active
- Transition: All properties, 300ms

**Secondary (Outline)**
```html
<button class="border-2 border-gray-300
               hover:bg-gray-50
               rounded-2xl">
```
- Used for: Secondary actions
- Lighter visual weight

**Ghost (Hidden until hover)**
```html
<button class="opacity-0 group-hover:opacity-100
               transition-opacity duration-200">
```
- Used for: Delete, Download on document cards
- Appears only when parent is hovered

### Progress Bars
```html
<div class="h-2 bg-gray-100 rounded-full overflow-hidden">
  <div class="h-full bg-gradient-to-r from-blue-500 to-indigo-600"
       style="width: {percentage}%">
  </div>
</div>
```
- Smooth width transitions
- Gradient fill for visual appeal

---

## Animations & Transitions

### Hover Effects
- **Cards**: `hover:shadow-lg` - Subtle elevation
- **Buttons**: `hover:shadow-xl` - Dramatic elevation
- **Icons**: `group-hover:scale-105` - Gentle growth

### Loading States
- **Spinner**: `animate-spin` - Continuous rotation
- **Pulse**: `animate-pulse` - Opacity fade in/out
- **Progress**: Width transition over 300ms

### State Changes
```css
All transitions: transition-all duration-300
Opacity: transition-opacity duration-200
Transform: transition-transform duration-300
```

---

## Responsive Design

### Breakpoints (Tailwind defaults)
```css
sm:  640px  - Small tablets
md:  768px  - Tablets
lg:  1024px - Laptops
xl:  1280px - Desktops
2xl: 1536px - Large screens
```

### Responsive Patterns

**Hero Section:**
```html
<h1 class="text-4xl md:text-6xl">
```
- Mobile: 36px (text-4xl)
- Desktop: 60px (md:text-6xl)

**Grid Layouts:**
```html
<div class="grid gap-8 md:grid-cols-3">
```
- Mobile: 1 column (stacked)
- Tablet+: 3 columns (side-by-side)

**Buttons:**
```html
<div class="flex flex-col sm:flex-row gap-4">
```
- Mobile: Stacked vertically
- Small screens+: Horizontal

---

## Accessibility Features

### Semantic HTML
```html
<button>   - For all clickable actions
<input>    - For all form controls
<label>    - For all inputs (including checkboxes)
<svg>      - For all icons
```

### Form Controls
```html
<input type="checkbox"
       id="select-all-documents"
       name="select-all"
       class="...">
<label for="select-all-documents">
  Select all documents
</label>
```
- All inputs have `id` and `name`
- All inputs have associated `<label>`
- Proper `for` attributes

### Focus States
```css
focus:ring-indigo-500 - Clear focus indicator
focus:ring-2          - Adequate thickness
```

### Color Contrast
- All text meets WCAG AA standards
- Status colors chosen for distinctiveness
- Icon + text labels for status (not color alone)

---

## Implementation Notes

### Technology Stack
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first styling (via CDN)
- **Vanilla JavaScript** - Tab switching, toggles
- **SVG Icons** - Crisp at any resolution

### No Dependencies
The mockup is completely standalone:
- ✅ No build process
- ✅ No npm packages
- ✅ No framework required
- ✅ Works offline
- ✅ Single file deployment

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

---

## User Flows

### Upload Flow
```
1. User lands on Upload tab (default)
2. Sees hero + template toggle + dropzone
3. Clicks/drags file to dropzone
4. Upload progress cards appear
5. Progress bars update in real-time
6. Success state shows checkmark
7. Auto-switches to Documents tab (in real app)
```

### Document Management Flow
```
1. User clicks Documents tab
2. Sees library of processed documents
3. Can select individual docs via checkbox
4. Can select all via header checkbox
5. Download button activates when selection > 0
6. Hovers over document to see actions
7. Clicks download for Excel export
8. Or clicks delete to remove
```

### Template Mode Flow
```
1. User enables template mode toggle
2. Info panel expands explaining behavior
3. Uploads multiple documents
4. All process in template mode
5. Switches to Documents tab
6. Sees "Download Template" button
7. Downloads consolidated Excel with all data
```

---

## Design Patterns

### Card Pattern
```html
<div class="group p-6 border rounded-2xl
            hover:shadow-lg transition-all">
  <!-- Content -->
  <div class="opacity-0 group-hover:opacity-100">
    <!-- Hidden actions -->
  </div>
</div>
```
- Used throughout for consistency
- Always includes hover effect
- Hidden actions revealed on hover

### Gradient Icon Pattern
```html
<div class="flex items-center justify-center
            w-12 h-12 rounded-2xl
            bg-gradient-to-br from-{color}-500 to-{color}-600
            text-white">
  <svg>...</svg>
</div>
```
- Consistent sizing (48px / w-12 h-12)
- Always uses gradient background
- White icons for contrast
- Rounded corners (rounded-2xl)

### Status Badge Pattern
```html
<div class="flex items-center gap-2
            px-3 py-1 rounded-xl
            bg-{color}-50 text-{color}-700">
  <StatusIcon class="w-4 h-4" />
  <span>Status Text</span>
</div>
```
- Icon + text for clarity
- Color-coded background
- Compact sizing (sm text, small padding)

---

## Future Enhancements

### Planned Features
- [ ] **Dark mode** - Toggle between light/dark themes
- [ ] **Drag & drop** - Actual file drag-and-drop functionality
- [ ] **Real-time updates** - WebSocket integration for live progress
- [ ] **Keyboard shortcuts** - Power user efficiency
- [ ] **Advanced filters** - Filter documents by status, date
- [ ] **Search** - Find documents by filename
- [ ] **Sorting** - Sort by date, name, status, pages

### Potential Improvements
- Skeleton loading states
- Empty state illustrations
- Onboarding tooltips
- Achievement/progress indicators
- Batch retry for failed uploads
- Advanced Excel export options

---

## Development Reference

### Using in Production

The actual frontend is built with:
```bash
# Technology Stack
- Next.js 14 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- React Query (data fetching)
- Axios (HTTP client)
```

To see the live version:
```bash
# Start the full app
docker-compose up -d

# Frontend only
cd frontend && npm run dev

# Access at http://localhost:3000
```

### Component Mapping

**Mockup → Real Component:**
- Upload Zone → `components/document-uploader.tsx`
- Document List → `components/document-list.tsx`
- Main Page → `app/page.tsx`
- Tabs → `components/ui/tabs.tsx`
- Buttons → `components/ui/button.tsx`
- Progress → `components/ui/progress.tsx`

---

## Credits

**Design Inspiration:**
- [Tailwind UI](https://tailwindui.com/) - Component patterns
- [Shadcn UI](https://ui.shadcn.com/) - Design system
- [Lucide Icons](https://lucide.dev/) - Icon library

**Built with:**
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [Claude Code](https://claude.com/claude-code) - AI assistance

---

## Mockup Screenshots

### Full Page Views

**Upload Tab - Default State**
- Clean, inviting interface
- Clear call-to-action
- Professional gradient design

**Upload Tab - Active Upload**
- Real-time progress indicators
- Multiple file handling
- Error states with retry

**Documents Tab - Library View**
- Grid of document cards
- Bulk selection
- Quick actions on hover

**Template Mode - Enabled**
- Info panel expanded
- Visual distinction from normal mode
- Clear explanation of benefits

---

## Getting Help

**Questions about the UI?**
- See main [README.md](../README.md)
- Check [DOCKER_SETUP.md](../DOCKER_SETUP.md) for running the real app
- Review [CONTRIBUTING.md](../CONTRIBUTING.md) for development

**Found a design issue?**
- Open an issue on GitHub
- Include screenshots
- Describe expected vs actual behavior

---

**Last Updated:** October 2025
**Mockup Version:** 1.0.0
**Real App Version:** See package.json
