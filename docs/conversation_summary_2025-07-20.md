# G-code Debugger – Conversation & Plan Summary (updated 2025-07-20)

## 1. Context & Goals
The application is a Tkinter-based G-code Debugger that connects to a Buildbotics controller via WebSocket and REST.  Recent work focused on:

* Eliminating segmentation faults caused by unsafely updating the UI from background threads.
* Achieving a **stable WebSocket connection** that auto-reconnects and updates the UI status label (green "Connected" / red "Not Connected").
* Allowing end-users to work with **external macros**:
  * All macros stored on the controller should appear in the "External Macros" list.
  * A single-click on a macro loads its code into the **debugger panel** (with unsaved-changes prompts).
  * Users can edit and save macros; delete is only allowed through the UI.
* Adding **bi-directional synchronisation** between the controller and a user-defined external-macros directory, with conflict resolution based on the most-recent timestamp.
* Because the controller does **not** run an NTP service (port 123 closed), the app must first compare clocks, warn if they differ by >2 s and compensate for the offset while deciding which macro copy is newer.

---

## 2. Implementation Status (20 Jul 2025)

### WebSocket
* Refactored `BBCtrlCommunicator._run_websocket` for robust error handling and reconnection.
* Removed unsupported `socket_timeout` arg; fixed stray except blocks.
* Added keep-alive ping thread and cleaned shutdown.

### UI Improvements
* Status label now shows **“Status: Connected”** (bright green) or **“Status: Not Connected”** (bright red).
* Main window centres on start-up; panels remember sizes.

### Macro synchronisation groundwork
* New REST helpers in `core/communication.py`:
  * `get_controller_time()` – tries `/api/time`, falls back to HTTP `Date:` header.
  * `upload_macro(name, data)` – PUT/POST macro JSON.
  * `delete_macro_on_controller(name)` – DELETE macro.
* Planned (not yet implemented) `MacroManager.sync_bidirectional(offset)` that:
  1. Gets Δ (clock offset) from controller.
  2. Downloads macro list; compares timestamps (after offset correction).
  3. Uploads newer local files, downloads newer remote files.
  4. Leaves duplicates untouched when times are equal within ε (1 s).
* Deletion logic will call both local removal and `delete_macro_on_controller()`.

---

## 3. Current Task List

- [x] Eliminate segmentation fault after WebSocket disconnects/reconnects.
- [x] Fix WebSocketApp instantiation & unsupported args.
- [x] Polish status label.
- [ ] **Implement robust bi-directional macro sync**
  - [ ] Compute clock offset; warn if >2 s.
  - [ ] `MacroManager.sync_bidirectional()` with newest-wins logic.
  - [ ] 🔄 Manual "Sync" button in Macro panel.
  - [ ] Deletion only via UI and propagated to controller.
  - [ ] Validate list refresh shows all macros.
- [ ] Validate overall stability (WebSocket, UI thread safety, macro sync).

---

## 4. Next Steps
1. Implement `MacroManager.sync_bidirectional()` using the new REST helpers.
2. Integrate it into the start-up background thread and add manual sync button.
3. Update Macro delete button to call both local & controller deletion.
4. Extensive testing with controller online/offline and with clock drift scenarios.

---

*Generated automatically by Cascade assistant.*
