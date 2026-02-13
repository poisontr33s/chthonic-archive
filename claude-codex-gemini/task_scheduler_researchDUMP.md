# **Operational Architecture of Unattended GPU Workloads on Windows Systems: Session Isolation, Driver Models, and Power Management**

## **1\. Introduction: The Paradigm Conflict of Headless Windows Computing**

The utilization of Microsoft Windows as a platform for high-performance, unattended graphics processing unit (GPU) workloads represents a fundamental conflict between operating system design intent and modern computational deployment patterns. Windows, in its consumer and workstation iterations (Windows 10, Windows 11\) and even in its server variants, is architecturally predicated on the concept of an "interactive session"—a state where a human user, physically present or remotely connected, interacts with a graphical shell. The entire graphics subsystem, from the kernel-mode driver to the user-mode API surface, is optimized to prioritize the responsiveness, power efficiency, and security of this interactive display environment.1

However, the contemporary landscape of GPU computing has shifted dramatically toward unattended execution. Organizations increasingly deploy Windows nodes for render farms, automated machine learning training loops, continuous integration/continuous deployment (CI/CD) testing pipelines involving graphical user interface (GUI) automation (e.g., Selenium), and decentralized cryptographic processing. These tasks require the GPU to perform heavy lifting—rendering 3D scenes via Direct3D, executing CUDA kernels, or accelerating browser engines—without a monitor attached and often without a user logged in.3

This operational requirement collides with three specific architectural pillars of the Windows ecosystem: **Session 0 Isolation**, **Windows Display Driver Model (WDDM) dependency on display output**, and **Client-focused Power Management**.

Session 0 Isolation, a security boundary introduced in Windows Vista to prevent "shatter attacks," explicitly decouples system services (background tasks) from the interactive graphics stack. This separation effectively renders standard GPU acceleration APIs inaccessible to tasks triggered by the Windows Task Scheduler or system services unless specific, often undocumented, bypasses are employed.2

Simultaneously, the WDDM driver architecture—the standard for all GeForce and most Quadro/RTX GPUs—is designed to aggressively conserve power or unload driver resources when no display sink (monitor) is detected. This "headless" state frequently results in context loss, where the GPU driver refuses to accept commands or resets the operational context, causing automated jobs to fail with cryptic errors typically associated with device removal.6

Finally, Windows power management policies, specifically those governing "Modern Standby" and "Unattended Sleep," are tuned to aggressive power-saving measures that prioritize battery life and thermal management over sustained background throughput. Hidden registry settings can cause systems to suspend operations minutes after waking for a scheduled task, silently terminating long-running renders or computations.8

This report provides an exhaustive technical analysis of these friction points. It deconstructs the mechanisms of Session 0 Isolation, contrasts the WDDM and TCC driver models, evaluates hardware and software emulation strategies for headless operation, and details the precise registry and power plan configurations necessary to stabilize unattended GPU workflows. It serves as a definitive architectural guide for systems engineers tasked with deploying robust Windows-based GPU compute clusters.

## **2\. Session 0 Isolation: The Architectural Barrier to GPU Acceleration**

To understand why a simple script running under Task Scheduler fails to render 3D graphics, one must examine the evolution of the Windows Session architecture. The failure is not a bug, but a deliberate security feature that creates a chasm between background automation and the graphics hardware.

### **2.1 Historical Context: The Shatter Attack and the Vista Pivot**

In versions of Windows prior to Vista (e.g., Windows XP, Server 2003), system services and the first locally logged-on user shared the same session—**Session 0**. This meant that a service running with SYSTEM privileges could create a window on the interactive user's desktop. While convenient for interoperability, this architecture was vulnerable to the "Shatter Attack." A malicious user could send a Windows message (like WM\_TIMER or WM\_SETTEXT) to a privileged service's window, forcing the service to execute arbitrary code with SYSTEM level permissions, effectively granting the attacker full control over the machine.2

With the release of Windows Vista, Microsoft introduced **Session 0 Isolation**. Under this model, Session 0 is reserved exclusively for system services and non-interactive drivers. The first interactive user is forced into **Session 1** (or higher). This isolation creates a strict boundary: services in Session 0 cannot send messages to, or draw windows on, the desktop of the user in Session 1\.5

### **2.2 The Impact on GPU Context Creation**

The isolation of Session 0 has profound implications for GPU acceleration. The Windows graphics subsystem, specifically the initialization of DirectX and OpenGL contexts, relies heavily on the presence of a "Window Station" (WinSta0) and a "Desktop" capable of receiving input and displaying output.

In an interactive session (Session 1+), the **Desktop Window Manager (DWM)** is the compositing engine that manages the visual state of the windows. DWM loads the GPU drivers and facilitates hardware acceleration for the graphical shell. However, in Session 0, the environment is fundamentally different:

1. **No DWM:** The Desktop Window Manager does not run in Session 0 in the same capacity as it does in user sessions. The graphical capabilities are limited to a legacy implementation necessary only for rudimentary service compatibility.  
2. **Limited Window Station:** Services run in a non-interactive window station. When an application attempts to create a Direct3D device (e.g., D3D11CreateDevice), the API often looks for a valid adapter associated with the current session's display output.  
3. **Driver Fallback:** Because WDDM drivers are optimized for DWM-managed desktops, attempting to initialize them in Session 0 often results in failure or a fallback to the **Microsoft Basic Render Driver** (software rasterization). This software fallback is functional for basic 2D drawing but completely inadequate for heavy 3D rendering or CUDA workloads, leading to abysmal performance or application crashes.1

The research snippet highlights communication with the Microsoft LogonSDK team, confirming that "it is not possible to fully impersonate an interactive user programmatically... session 0 isolation was the root cause of the regression." This confirms that even if a service attempts to impersonate a user account, if the process originates in Session 0, it does not inherit the graphical "seat" required for full hardware acceleration.

### **2.3 The Deprecation of Interactive Services Detection**

Initially, Microsoft provided a workaround: the **Interactive Services Detection (UI0Detect)** service. This service would detect if a Session 0 service was trying to show a GUI and would prompt the user to "View the message," temporarily switching the user's screen to the Session 0 desktop.

However, as of Windows 10 Version 1803 and Server 2019, this capability has been deprecated and effectively removed.5 The service generally fails to start, and the registry hacks that previously enabled it (setting NoInteractiveServices to 0\) are no longer reliable. This cements the reality that **Session 0 is a black hole for graphics**. Any robust architecture for unattended GPU tasks must avoid running the actual rendering process in Session 0\.

### **2.4 Task Scheduler Contexts and the "Hidden" Trap**

The Windows Task Scheduler is the primary interface where administrators encounter Session 0 issues. The behavior of a task is dictated entirely by the security options selected during its creation:

* **"Run only when user is logged on"**: This option attaches the task to the user's existing interactive session (e.g., Session 1). The application launches on the visible desktop, has full access to the GPU via DWM, and behaves like a manually started program. The critical limitation is that if the machine reboots and sits at the Lock Screen or Login Screen, the session does not exist, and the task will not run.11  
* **"Run whether user is logged on or not"**: This option creates a "batch logon" session for the task. This session is non-interactive and shares many characteristics with Session 0\. It does not have an associated monitor output. Consequently, GPU drivers typically fail to initialize, and the virtual screen resolution defaults to a fail-safe (often 1024x768 or 0x0), which breaks UI automation scripts that expect specific element coordinates.12

A common misconception is that checking the **"Hidden"** box in Task Scheduler fixes window management issues. In reality, as noted in 11, the "Hidden" attribute works differently depending on the logon type. For "Run whether user is logged on or not," the task is *already* hidden from any interactive desktop. For "Run only when user is logged on," the "Hidden" checkbox allows the task to run without a window appearing on the user's taskbar, but it still executes within the interactive session's context.

### **2.5 Implications for UI Automation (Selenium/Browsers)**

The impact of Session 0 isolation is particularly acute for browser automation tools like Selenium. Modern web browsers (Chrome, Edge) are heavily GPU-accelerated. When launched in a non-interactive session (Task Scheduler with "Run whether user is logged on or not"), the browser attempts to bind to a display driver that doesn't exist.

Research indicates two primary failure modes:

1. **Resolution Mismatch:** The headless session defaults to 1024x768. Responsive websites may hide navigation elements behind "hamburger menus" at this resolution, causing Selenium "Element Not Clickable" errors.12  
2. **Rendering Freeze:** The browser's GPU process may hang indefinitely waiting for a VSync signal that never comes, or crash due to the lack of a swap chain.

To mitigate this in non-interactive sessions, administrators are forced to use flags like \--headless, \--disable-gpu, and \--window-size=1920,1080.12 However, disabling the GPU defeats the purpose if the goal is to test WebGL performance or render complex canvas elements. Therefore, for true GPU-accelerated automation, the process must be injected into Session 1 (Interactive) rather than Session 0\.

## **3\. The Graphics Driver Ecosystem: WDDM, TCC, and MCDM**

The operating system's ability to utilize the GPU is mediated by the driver model. Understanding the distinction between the consumer-focused WDDM and the compute-focused TCC is critical for architectural planning.

### **3.1 WDDM (Windows Display Driver Model)**

WDDM is the standard driver architecture for Windows Vista through Windows 11\. It is designed to support the rich, composited desktop experience managed by DWM.

* **Architecture:** WDDM splits the driver into a user-mode driver (UMD) and a kernel-mode driver (KMD). The **VidPn (Video Present Network)** manager handles the topology of display outputs.14  
* **The Headless Flaw:** WDDM is inherently display-centric. It assumes that a GPU's primary purpose is to push pixels to a screen. If no display is detected (a "headless" state), the WDDM driver often enters a low-power state or fails to load the full driver stack required for DirectX/OpenGL. This is a deliberate design to reduce power consumption on laptops and desktops when monitors are disconnected.  
* **Session 0 Behavior:** WDDM drivers are effectively crippled in Session 0\. They cannot create the swap chains necessary for D3D rendering because there is no DWM surface to present to.

### **3.2 TCC (Tesla Compute Cluster)**

To address the limitations of WDDM for high-performance computing (HPC), NVIDIA introduced the TCC driver model for its Quadro and Tesla product lines.

* **Mechanism:** TCC completely bypasses the Windows graphics subsystem. It does not interface with DWM or DirectX. Instead, it exposes the GPU strictly as a CUDA compute device.15  
* **Advantages for Unattended Tasks:**  
  * **Session 0 Compatibility:** Because TCC does not rely on a window station or display output, it functions perfectly within Session 0\. A Windows Service running as SYSTEM can fully utilize a TCC GPU for CUDA workloads.15  
  * **Remote Desktop Support:** Since the TCC GPU is not "driving" the desktop display, using Remote Desktop (RDP) to access the server does not interfere with the GPU's operation. In contrast, RDP often replaces the WDDM driver with the "Remote Desktop Display Driver," disabling consumer GPUs.1  
  * **Performance:** TCC eliminates the overhead of the WDDM scheduler (although WDDM 2.x has reduced this gap significantly with hardware scheduling).17  
* **Limitations:**  
  * **No Graphics APIs:** TCC supports CUDA and OpenCL only. It *cannot* run DirectX, OpenGL, or Vulkan applications. If the workload involves rendering (e.g., a game engine or 3D rendering software that uses Direct3D), TCC is useless.18  
  * **Hardware Restriction:** TCC is artificially restricted to NVIDIA's professional GPUs (Tesla, Quadro, and specific Titan cards). It is **not available** on GeForce consumer cards (e.g., RTX 3090, 4090). This forces users of consumer hardware to battle WDDM limitations.17

### **3.3 Switching Driver Models**

For supported hardware (e.g., NVIDIA A40, A6000), the driver mode can be toggled using the NVIDIA System Management Interface (nvidia-smi) tool. This requires a system reboot.

| Command | Action | Description |
| :---- | :---- | :---- |
| nvidia-smi \-dm 0 | Set to WDDM | Enables graphics, DirectX, and display output. Default for Quadro. |
| nvidia-smi \-dm 1 | Set to TCC | Enables compute-only mode. Disables display output. Default for Tesla. |

Citation: 18

It is important to note that Tesla cards (e.g., T4, A100) often default to TCC. If a user intends to use them for Virtual Workstations (vGPU) or cloud gaming where DirectX is required, they must explicitly switch the card to WDDM mode and often require a **GRID vGPU license** to unlock graphics functionality.3 Without this license, switching a Tesla card to WDDM may fail or result in restricted functionality.

### **3.4 MCDM (Microsoft Compute Driver Model)**

Introduced in WDDM 2.6 (Windows 10 1903), MCDM is a subset of WDDM designed for "compute-only" devices, primarily NPU (Neural Processing Units) and specialized accelerators.22

* **Intent:** It allows a device to exist in the WDDM ecosystem without exposing a display output (VidPn).  
* **Status:** While promising for the future of headless computing, MCDM is not currently a user-selectable mode for standard NVIDIA/AMD GPUs. Users cannot simply "switch" a GeForce card to MCDM to simulate TCC behavior. It requires specific driver support from the vendor, which is largely absent for consumer graphics cards.20

### **3.5 DirectX 12 Agility SDK and Headless Enhancements**

Recent developments in the DirectX 12 Agility SDK (WDDM 3.0+) have introduced features to improve headless rendering, particularly **Direct3D 12 Video Encoding** and enhanced barrier synchronization.7

* **Video Encoding:** Allows video encode/decode operations to happen on the GPU without a display head, useful for headless cloud render nodes.  
* **Dirty Bit Tracking (WDDM 3.2):** Improves performance for live migration of virtual machines using vGPU, relevant for cloud environments like Azure Virtual Desktop.25 Despite these improvements, the fundamental requirement for a valid WDDM session context remains for most legacy DirectX 11/12 graphics applications.

## **4\. Workarounds for Headless WDDM Execution**

For the vast majority of users who cannot use TCC mode—either because they rely on graphics APIs (DirectX/OpenGL) or because they use consumer GeForce hardware—the challenge is to "trick" the WDDM driver into remaining active and performant in a headless, potentially unattended environment.

### **4.1 Hardware Emulation: The EDID Dummy Plug**

The most robust solution for headless WDDM operation is the **HDMI/DisplayPort Dummy Plug** (often called a "Headless Ghost").

* **Mechanism:** These small dongles plug into the GPU's video output ports. They contain an EEPROM chip programmed with **EDID (Extended Display Identification Data)** information. This data tells the GPU that a monitor is connected, specifying its resolution (e.g., 4K @ 60Hz), refresh rate, and color depth.26  
* **Effect on Windows:**  
  * **Driver Persistence:** The GPU detects a valid display sink. The WDDM driver loads fully and remains active.  
  * **Resolution Control:** Windows allows the user to set the desktop resolution to match the dummy plug (e.g., 3840x2160). This is critical for remote desktop tools (TeamViewer, Parsec, AnyDesk), which capture the framebuffer content. Without a dummy plug, these tools often default to 640x480 or fail to connect entirely.28  
  * **Prevention of Context Loss:** When a physical monitor is turned off, it often stops sending EDID. Windows detects this "hotplug" event and may disable the display output, causing running graphical applications to crash (Context Loss). A dummy plug provides a constant, unswerving signal, immune to power saving on the monitor side.26

### **4.2 Software Emulation: Virtual Display Drivers (IddCx)**

For cloud instances (AWS, Azure) or physical servers located in remote data centers where physical access to plug in a dongle is impossible, software-based **Indirect Display Drivers (IDD)** are the modern solution.

* **The IddCx Framework:** Microsoft introduced the Indirect Display Driver Class Extension (IddCx) to allow devices (like USB docks or Wi-Fi displays) to create monitors that don't physically connect to the GPU's display outputs.  
* **Virtual Display Driver (VDD):** An open-source project 30 leverages IddCx to create a fully virtual monitor in Windows.  
  * **Capabilities:** It allows users to add one or more virtual displays with custom resolutions (up to 4K/8K) and high refresh rates (120Hz+).  
  * **HDR Support:** As of recent updates (Windows 11 23H2+), VDD supports HDR (High Dynamic Range), allowing for the testing and streaming of HDR content on headless servers.30  
  * **Headless Operation:** By installing VDD, the system believes a monitor is attached. This satisfies the WDDM requirement, keeping the GPU active and allowing DWM to compose the desktop. This is particularly popular for "Sunshine/Moonlight" game streaming setups on headless servers.31

### **4.3 Orchestration: Breaking the Session Boundary with PsExec**

If a task must be triggered by a system service (like a Jenkins Agent, a GitLab Runner, or a startup script) but *must* run in the Interactive Session (Session 1\) to access the WDDM driver, **PsExec** is the industry-standard tool for "Session Breakout."

* **The Constraint:** A service running as SYSTEM in Session 0 cannot simply launch renderer.exe. If it does, renderer.exe runs in Session 0 and fails.  
* **The Solution:** Use PsExec to launch the process *into* Session 1\.  
* **Command Syntax:**  
  DOS  
  psexec.exe \-i 1 \-u \<Username\> \-p \<Password\> "C:\\Path\\To\\Application.exe"

  * **\-i \<SessionID\>**: This switch is crucial. It tells PsExec to run the application interactively in the specified session. \-i alone might default to the current session or Session 0\. Specifying 1 (or the actual ID of the logged-in user) forces the process onto the user's desktop.10  
  * **\-u / \-p**: While SYSTEM can technically write to Session 1, many applications rely on a specific user profile (User Registry Hive, AppData). Impersonating the logged-in user ensures the application finds its configuration files.34  
* **Identifying the Session ID:** The ID is not always 1\. On a server with multiple RDP connections, it could be 2, 3, etc. Robust scripts use the query user or quser command to dynamically parse the ID of the active user:  
  PowerShell  
  $sessionID \= (quser /server:localhost | Where-Object { $\_ \-match 'Active' } | ForEach-Object { $\_.Split(' ',::RemoveEmptyEntries) })  
  & psexec.exe \-i $sessionID \-u Admin \-p Password "app.exe"

  33  
* **Security Warning:** Microsoft Defender's Attack Surface Reduction (ASR) rules in Windows 11 24H2 and Server 2025 include a rule to "Block process creations originating from PSExec and WMI commands." In high-security environments, this rule must be set to "Audit" or disabled to allow this orchestration technique.36

## **5\. Power Management & The "Sleep" Conspiracy**

Even with a perfectly configured driver and session environment, Windows Power Management contains hidden mechanisms designed to aggressively suspend "idle" hardware. These mechanisms are the most frequent cause of "unexplained" failures in unattended GPU tasks.

### **5.1 The "System Unattended Sleep Timeout"**

This is arguably the most insidious setting in the Windows power ecosystem.

* **The Behavior:** When a computer is woken from sleep by a Scheduled Task (using a "Wake Timer"), Windows puts the system back to sleep after exactly **2 minutes** if no user interaction (keyboard/mouse) is detected. It ignores the standard "Sleep after 30 minutes" user setting.8  
* **The Impact:** A render job wakes the machine at 3:00 AM. The job starts. Two minutes later, the machine suspends, terminating the job mid-frame.  
* **The Solution:** This setting is **hidden** in the classic Control Panel by default. It must be unhidden via the Registry or PowerShell.  
  * **Registry Key:** HKEY\_LOCAL\_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\238C9FA8-0AAD-41ED-83F4-97BE242C8F20\\7bc4a2f9-d8fc-4469-b07b-33eb785aaca0  
  * **Attribute Modification:** Change the Attributes DWORD from 1 (Hidden) to 2 (Visible).38  
  * **Configuration:** Once visible, navigate to *Power Options \> Change plan settings \> Change advanced power settings \> Sleep \> System unattended sleep timeout*. Set this value to **0** (Never) or a duration longer than your longest task (e.g., 1440 minutes).

### **5.2 PCIe Link State Power Management (ASPM)**

Windows "Balanced" and even some "High Performance" plans enable Active State Power Management (ASPM) for the PCI Express bus.

* **Mechanism:** When the bus is idle (even for milliseconds between frames), the OS attempts to transition the link to a low-power state (L0s or L1).  
* **The Problem:** Waking the PCIe link introduces latency. For compute workloads involving frequent CPU-GPU transfers (like the Block Swapping described in 23), this latency can degrade performance significantly. More critically, the rapid transition between power states can destabilize the GPU driver, leading to TDR crashes or system freezes.40  
* **Recommendation:** Explicitly set "Link State Power Management" to **Off** in the Advanced Power Options. Furthermore, in the BIOS/UEFI, ensuring the PCIe slot is locked to "Gen4" or "Gen5" rather than "Auto" can prevent negotiation errors.41

### **5.3 Modern Standby (S0ix) vs. S3 Sleep**

Modern laptops and desktops (Surface devices, Dell XPS) utilize **Modern Standby (S0 Low Power Idle)** instead of the traditional S3 (Suspend to RAM) sleep.

* **Behavior:** When the screen is locked or the lid is closed, the system remains "on" but aggressively power-gates components. The OS may decide to cut power to the dGPU (discrete GPU) to save battery, even if a compute process is running.42  
* **Context Loss:** This power-gating often results in the CUDA context being destroyed. When the machine "wakes," the application has lost its connection to the VRAM.  
* **Mitigation:**  
  * **Disable Modern Standby:** This is difficult on modern hardware (requires BIOS hacks or OS reinstallation).  
  * **Prevent Sleep Entirely:** Use tools like PowerToys Awake or simple scripts that toggle the F15 key to prevent the idle timer from triggering S0ix.  
  * **Monitor Sleep:** Instead of locking the session (which triggers S0ix logic), configure the power plan to "Turn off display after X minutes" but "Put computer to sleep: Never." Use a virtual display driver or dummy plug to ensure the "Display Off" state doesn't actually disconnect the virtual monitor signal.

### **5.4 Desktop Window Manager (DWM) Throttling on Lock**

When a user locks the workstation (Win \+ L), Windows deprioritizes the DWM and interactive processes to save resources.

* **Observation:** Users report DWM GPU usage spiking or GPU clocks fluctuating wildly when the screen is locked.44 This is often due to the DWM attempting to compose the Lock Screen UI while simultaneously managing the background desktop.  
* **Solution:** For render nodes, it is often better to **not lock the session**. Instead, use a physical security measure (locked server room) or disconnect the keyboard/mouse. If locking is mandatory, ensuring "Hardware Accelerated GPU Scheduling" (HAGS) is disabled can sometimes stabilize the DWM behavior in the locked state.45

## **6\. Stability Tweaks: Timeout Detection and Recovery (TDR)**

The **Timeout Detection and Recovery (TDR)** feature is a watchdog mechanism in Windows designed to prevent a frozen GPU from locking up the entire system. However, for GPGPU (General-Purpose computing on GPU) tasks, TDR is often a hindrance.

### **6.1 The Mechanism of TDR**

The OS scheduler monitors the GPU. If a graphics card takes longer than **2 seconds** to complete a single preemptible operation (a "packet"), Windows assumes the hardware has hung. It then attempts to reset the GPU driver to recover the desktop.47

* **The Conflict:** In rendering (Redshift, Octane, V-Ray) or simulation (Ansys, CUDA), a single frame or calculation step can easily take 5, 10, or 60 seconds. TDR sees this as a hang and kills the driver, crashing the application.48

### **6.2 Registry Configuration for Compute Stability**

To prevent TDR from killing legitimate long-running tasks, administrators must modify the Windows Registry. These keys are located at HKEY\_LOCAL\_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers.

**Table 1: Essential TDR Registry Keys**

| Registry Value | Type | Default | Recommended (Compute) | Description |
| :---- | :---- | :---- | :---- | :---- |
| **TdrDelay** | REG\_DWORD | 2 (sec) | **60** or **120** | Specifies the number of seconds the GPU can delay the preempt request from the GPU scheduler before the OS considers it hung. |
| **TdrDdiDelay** | REG\_DWORD | 5 (sec) | **60** or **120** | Specifies the time allowed for a thread to leave the driver. Should typically match or exceed TdrDelay. |
| **TdrLevel** | REG\_DWORD | 3 | **3** (or 0\) | Level of recovery. '3' recovers on timeout. '0' disables detection entirely (use with caution; system will freeze if GPU actually hangs). |

Citation: 48

**Implementation Note:** Changes to these keys require a system restart to take effect. If TdrDelay does not exist, it must be created. Setting these values too high (e.g., 3600 seconds) effectively disables TDR, meaning if a true hardware fault occurs, the machine will remain frozen indefinitely, requiring a hard reboot. A value of 60-120 seconds is a balanced safe harbor for most rendering tasks.

### **6.3 HAGS (Hardware Accelerated GPU Scheduling)**

Introduced in WDDM 2.7, HAGS shifts memory management tasks from the CPU to the GPU.

* **Stability Impact:** While HAGS improves gaming FPS, it has been linked to instability in OpenCL and CUDA workloads and erratic DWM behavior on Windows 11\.28  
* **Recommendation:** If unexplained crashes occur despite TDR tuning, disable HAGS via *Settings \> System \> Display \> Graphics \> Change default graphics settings*.

## **7\. Strategic Implementation Guide**

Based on the architectural constraints and workarounds detailed above, three distinct configurations are recommended depending on the hardware and use case.

### **Scenario A: The Enterprise Compute Node (NVIDIA Tesla/Data Center)**

* **Hardware:** NVIDIA A10, A40, A100, H100.  
* **Driver Model:** **TCC Mode** (Enabled via nvidia-smi \-dm 1).  
* **Session:** Service (Session 0\) or Interactive.  
* **Orchestration:** Standard Task Scheduler ("Run whether user is logged on or not") or Windows Services.  
* **Advantage:** Completely bypasses WDDM, DWM, and Session 0 limitations.  
* **Disadvantage:** No DirectX/OpenGL graphics support. Pure compute only.

### **Scenario B: The "Prosumer" Render Farm (GeForce/Quadro WDDM)**

* **Hardware:** GeForce RTX 4090, RTX 6000 Ada (in WDDM mode).  
* **Driver Model:** WDDM (Default).  
* **Session:** **Session 1 (Interactive)**.  
* **Headless Handling:** **HDMI Dummy Plug** or **Virtual Display Driver**.  
* **Power:** "High Performance" Plan. "System unattended sleep timeout" set to 0\.  
* **Orchestration:**  
  * **AutoLogon:** Configure Sysinternals AutoLogon to ensure a user is always signed in after reboot.  
  * **Task Launch:** Use a startup script in shell:startup (if the task runs constantly) or Task Scheduler configured to **"Run only when user is logged on."**  
  * **Remote Launch:** If triggering from a remote service, use **PsExec** with \-i 1 to inject the process into the user session.

### **Scenario C: The UI Automation Node (Selenium/Browsers)**

* **Hardware:** Any WDDM GPU.  
* **Session:** **Session 1 (Interactive)**.  
* **Configuration:**  
  * **Resolution:** Ensure the Dummy Plug/Virtual Display is set to 1920x1080 or higher.  
  * **Browser Flags:** Avoid \--headless if possible to test true rendering; rely on the dummy display to provide the surface.  
  * **Scaling:** Ensure Windows Display Scaling is set to 100% to prevent coordinate offset errors in Selenium click events.

## **8\. Conclusion**

The successful deployment of unattended GPU workloads on Windows requires a deliberate departure from standard desktop management practices. The operating system's default security posture (Session 0 Isolation) and power posture (Modern Standby, WDDM headless throttling) are actively hostile to background compute tasks.

For pure compute workloads, the **TCC driver model** provides the only clean architectural solution, severing the bond between the GPU and the Windows graphical subsystem. However, for the vast majority of mixed workloads involving consumer hardware or graphics APIs, the solution lies in **mimicking interactivity**. By employing hardware EDID emulators to satisfy WDDM display requirements, utilizing PsExec to breach the Session 0 boundary, and surgically modifying the registry to disable unattended sleep timeouts and extend TDR thresholds, systems administrators can coerce the Windows client OS into functioning as a reliable high-performance compute node.

#### **Referanser**

1. Enabling GPU Rendering for Microsoft Remote Desktop \- \- CivilGEO Knowledge Base, brukt februar 13, 2026, [https://knowledge.civilgeo.com/enabling-gpu-rendering-for-microsoft-remote-desktop/](https://knowledge.civilgeo.com/enabling-gpu-rendering-for-microsoft-remote-desktop/)  
2. Windows 2008 RenderFarm Service: CreateProcessAsUser ..., brukt februar 13, 2026, [https://stackoverflow.com/questions/2464182/windows-2008-renderfarm-service-createprocessasuser-session-0-isolation-and-o](https://stackoverflow.com/questions/2464182/windows-2008-renderfarm-service-createprocessasuser-session-0-isolation-and-o)  
3. GPU acceleration for Windows multi-session OS | Citrix Virtual Apps and Desktops™ 7 2203 LTSR, brukt februar 13, 2026, [https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/2203-ltsr/graphics/hdx-3d-pro/gpu-acceleration-server.html](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/2203-ltsr/graphics/hdx-3d-pro/gpu-acceleration-server.html)  
4. Enable GPU acceleration for Azure Virtual Desktop \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/azure/virtual-desktop/graphics-enable-gpu-acceleration](https://learn.microsoft.com/en-us/azure/virtual-desktop/graphics-enable-gpu-acceleration)  
5. Manually Enabling Session 0 Interactive Services Detection, brukt februar 13, 2026, [https://kb.firedaemon.com/support/solutions/articles/4000106823-manually-enabling-interactive-services-interactive-service-detection-and-session-0](https://kb.firedaemon.com/support/solutions/articles/4000106823-manually-enabling-interactive-services-interactive-service-detection-and-session-0)  
6. Windows 11 Pro security update KB5074109 messed up GPU rendering \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-ca/answers/questions/5708599/windows-11-pro-security-update-kb5074109-messed-up](https://learn.microsoft.com/en-ca/answers/questions/5708599/windows-11-pro-security-update-kb5074109-messed-up)  
7. WDDM Overview \- Windows drivers | Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/windows-vista-display-driver-model-design-guide](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/windows-vista-display-driver-model-design-guide)  
8. Windows 11 23H2 \- System goes back to sleep (AFTER waking) in 2 Minutes, brukt februar 13, 2026, [https://www.elevenforum.com/t/windows-11-23h2-system-goes-back-to-sleep-after-waking-in-2-minutes.21732/](https://www.elevenforum.com/t/windows-11-23h2-system-goes-back-to-sleep-after-waking-in-2-minutes.21732/)  
9. WindowsPowerShell/Modules/Scripts/Set-SleepSchedule.ps1 at main \- GitHub, brukt februar 13, 2026, [https://github.com/stevencohn/WindowsPowerShell/blob/main/Modules/Scripts/Set-SleepSchedule.ps1](https://github.com/stevencohn/WindowsPowerShell/blob/main/Modules/Scripts/Set-SleepSchedule.ps1)  
10. Escalate program out of Session 0 \- c++ \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/17869522/escalate-program-out-of-session-0](https://stackoverflow.com/questions/17869522/escalate-program-out-of-session-0)  
11. Task Scheduler runs as hidden, how to make it visible? \- Server Fault, brukt februar 13, 2026, [https://serverfault.com/questions/251733/task-scheduler-runs-as-hidden-how-to-make-it-visible](https://serverfault.com/questions/251733/task-scheduler-runs-as-hidden-how-to-make-it-visible)  
12. selenium \- screen resolution in mode "Run whether user is logged ..., brukt februar 13, 2026, [https://stackoverflow.com/questions/26299936/screen-resolution-in-mode-run-whether-user-is-logged-on-or-not-in-windows-tas](https://stackoverflow.com/questions/26299936/screen-resolution-in-mode-run-whether-user-is-logged-on-or-not-in-windows-tas)  
13. Creating a web scraping program compatible with Windows task scheduler "run whether user is logged on or not" \- Stack Overflow, brukt februar 13, 2026, [https://stackoverflow.com/questions/65098767/creating-a-web-scraping-program-compatible-with-windows-task-scheduler-run-whet](https://stackoverflow.com/questions/65098767/creating-a-web-scraping-program-compatible-with-windows-task-scheduler-run-whet)  
14. GPU Virtual Memory in WDDM 2.0 \- Windows drivers | Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/gpu-virtual-memory-in-wddm-2-0](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/gpu-virtual-memory-in-wddm-2-0)  
15. Reference — Nsight Visual Studio Edition \- NVIDIA Documentation, brukt februar 13, 2026, [https://docs.nvidia.com/nsight-visual-studio-edition/reference/index.html](https://docs.nvidia.com/nsight-visual-studio-edition/reference/index.html)  
16. Designers or RDS sessions do not use the GPU \- NVIDIA Developer Forums, brukt februar 13, 2026, [https://forums.developer.nvidia.com/t/designers-or-rds-sessions-do-not-use-the-gpu/163148](https://forums.developer.nvidia.com/t/designers-or-rds-sessions-do-not-use-the-gpu/163148)  
17. Which NVIDIA Windows Driver do I need? WDDM vs. TCC \- YouTube, brukt februar 13, 2026, [https://www.youtube.com/watch?v=5nLhKhnQRjo](https://www.youtube.com/watch?v=5nLhKhnQRjo)  
18. Tesla Compute Cluster (TCC) \- NVIDIA Documentation, brukt februar 13, 2026, [https://docs.nvidia.com/nsight-visual-studio-edition/3.2/Content/Tesla\_Compute\_Cluster.htm](https://docs.nvidia.com/nsight-visual-studio-edition/3.2/Content/Tesla_Compute_Cluster.htm)  
19. Ray Tracing support unavailable on Windows Server 2022 with 3 NVidia A40 GPUs, brukt februar 13, 2026, [https://forums.developer.nvidia.com/t/ray-tracing-support-unavailable-on-windows-server-2022-with-3-nvidia-a40-gpus/266446](https://forums.developer.nvidia.com/t/ray-tracing-support-unavailable-on-windows-server-2022-with-3-nvidia-a40-gpus/266446)  
20. It turns out WDDM driver mode is making our RAM \- GPU transfer extremely slower compared to TCC or MCDM mode. Anyone has figured out the bypass NVIDIA software level restrictions? \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/StableDiffusion/comments/1ommmek/it\_turns\_out\_wddm\_driver\_mode\_is\_making\_our\_ram/](https://www.reddit.com/r/StableDiffusion/comments/1ommmek/it_turns_out_wddm_driver_mode_is_making_our_ram/)  
21. How to workaround TCC to WDDM on Nvidia Tesla cards : r/VFIO \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/VFIO/comments/p9zcwi/how\_to\_workaround\_tcc\_to\_wddm\_on\_nvidia\_tesla/](https://www.reddit.com/r/VFIO/comments/p9zcwi/how_to_workaround_tcc_to_wddm_on_nvidia_tesla/)  
22. Microsoft Compute Driver Model Overview \- Windows drivers, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/mcdm](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/mcdm)  
23. It turns out WDDM driver mode is making our RAM \- GPU transfer extremely slower compared to TCC or MCDM mode. Anyone has figured out the bypass NVIDIA software level restrictions? : r/LocalLLaMA \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/LocalLLaMA/comments/1ommahm/it\_turns\_out\_wddm\_driver\_mode\_is\_making\_our\_ram/](https://www.reddit.com/r/LocalLLaMA/comments/1ommahm/it_turns_out_wddm_driver_mode_is_making_our_ram/)  
24. What's New for Windows 11 Graphics Display Drivers \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/what-s-new-for-windows-11-display-and-graphics-drivers](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/what-s-new-for-windows-11-display-and-graphics-drivers)  
25. What's New in Driver Development for Windows 11, Version 24H2 \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/driver-changes-for-windows-11-version-24h2](https://learn.microsoft.com/en-us/windows-hardware/drivers/driver-changes-for-windows-11-version-24h2)  
26. This $3 HDMI dummy plug solved my headless server GPU problems \- XDA Developers, brukt februar 13, 2026, [https://www.xda-developers.com/this-hdmi-dummy-plug-solved-my-headless-server-gpu-problems/](https://www.xda-developers.com/this-hdmi-dummy-plug-solved-my-headless-server-gpu-problems/)  
27. When Does My GPU Server Need an HDMI Dummy Plug?, brukt februar 13, 2026, [https://www.gpu-mart.com/blog/when-we-need-an-hdmi-dummy-plug](https://www.gpu-mart.com/blog/when-we-need-an-hdmi-dummy-plug)  
28. Force a headless gaming PC to use the dedicated GPU to stream? : r/cloudygamer \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/cloudygamer/comments/w6k3yj/force\_a\_headless\_gaming\_pc\_to\_use\_the\_dedicated/](https://www.reddit.com/r/cloudygamer/comments/w6k3yj/force_a_headless_gaming_pc_to_use_the_dedicated/)  
29. Is this a dummy HDMI? One sided, what's the purpose of this? : r/VIDEOENGINEERING, brukt februar 13, 2026, [https://www.reddit.com/r/VIDEOENGINEERING/comments/1inb09w/is\_this\_a\_dummy\_hdmi\_one\_sided\_whats\_the\_purpose/](https://www.reddit.com/r/VIDEOENGINEERING/comments/1inb09w/is_this_a_dummy_hdmi_one_sided_whats_the_purpose/)  
30. VirtualDrivers/Virtual-Display-Driver: Add virtual monitors to ... \- GitHub, brukt februar 13, 2026, [https://github.com/itsmikethetech/Virtual-Display-Driver](https://github.com/itsmikethetech/Virtual-Display-Driver)  
31. Bought a dummy HDMI 2.1 plug to get 4K HDR streaming... but no HDR option now for new dummy 4K screen in Windows \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/MoonlightStreaming/comments/1fob94x/bought\_a\_dummy\_hdmi\_21\_plug\_to\_get\_4k\_hdr/](https://www.reddit.com/r/MoonlightStreaming/comments/1fob94x/bought_a_dummy_hdmi_21_plug_to_get_4k_hdr/)  
32. Why HDMI/Display port Dummy Plugs, and installing Virtual Display Driver \- YouTube, brukt februar 13, 2026, [https://www.youtube.com/watch?v=4nANsT9\_eNg](https://www.youtube.com/watch?v=4nANsT9_eNg)  
33. start exe in a Remote Session with PsExec \- pstools \- Server Fault, brukt februar 13, 2026, [https://serverfault.com/questions/357549/start-exe-in-a-remote-session-with-psexec](https://serverfault.com/questions/357549/start-exe-in-a-remote-session-with-psexec)  
34. How Do You Run GPU Task on Windows Server 2016 Remotely?, brukt februar 13, 2026, [https://serverfault.com/questions/990351/how-do-you-run-gpu-task-on-windows-server-2016-remotely](https://serverfault.com/questions/990351/how-do-you-run-gpu-task-on-windows-server-2016-remotely)  
35. Windows Internals, Part 1: System architecture, processes, threads, memory management, and more, brukt februar 13, 2026, [https://empyreal96.github.io/nt-info-depot/Windows-Internals-PDFs/Windows%20System%20Internals%207e%20Part%201.pdf](https://empyreal96.github.io/nt-info-depot/Windows-Internals-PDFs/Windows%20System%20Internals%207e%20Part%201.pdf)  
36. Tag:"guides" \- Microsoft Community Hub, brukt februar 13, 2026, [https://techcommunity.microsoft.com/tag/guides](https://techcommunity.microsoft.com/tag/guides)  
37. Windows 10 lock screen won't turn off \- Microsoft Q\&A, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/3209409/windows-10-lock-screen-wont-turn-off](https://learn.microsoft.com/en-us/answers/questions/3209409/windows-10-lock-screen-wont-turn-off)  
38. Windows 10 falls asleep after inactivity, even when I have chosen "never" fall asleep in settings : r/microsoft \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/microsoft/comments/tnq21t/windows\_10\_falls\_asleep\_after\_inactivity\_even/](https://www.reddit.com/r/microsoft/comments/tnq21t/windows_10_falls_asleep_after_inactivity_even/)  
39. Power Settings | PDF | Computer Science \- Scribd, brukt februar 13, 2026, [https://www.scribd.com/document/617448488/Power-Settings](https://www.scribd.com/document/617448488/Power-Settings)  
40. PCI Express \- Link State Power Management : r/overclocking \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/overclocking/comments/88i6kf/power\_management\_settings\_pci\_express\_link\_state/](https://www.reddit.com/r/overclocking/comments/88i6kf/power_management_settings_pci_express_link_state/)  
41. Weird GPU behavior after windows 10 clean install \- Microsoft Q\&A, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/3902240/weird-gpu-behavior-after-windows-10-clean-install](https://learn.microsoft.com/en-us/answers/questions/3902240/weird-gpu-behavior-after-windows-10-clean-install)  
42. psyq321/Dell5750FirmwareOptimizationRecipe: UEFI Firmware Optimization Recipe for Connected Standby and Low Temperature (Dell Precision 5750 and XPS 17\) \- GitHub, brukt februar 13, 2026, [https://github.com/psyq321/Dell5750FirmwareOptimizationRecipe](https://github.com/psyq321/Dell5750FirmwareOptimizationRecipe)  
43. Surface Book 3 dGPU overheating in sleep/idle \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/2294412/surface-book-3-dgpu-overheating-in-sleep-idle](https://learn.microsoft.com/en-us/answers/questions/2294412/surface-book-3-dgpu-overheating-in-sleep-idle)  
44. Excessive Windows DWM usage when screen is locked and display enters standby, brukt februar 13, 2026, [https://bugzilla.mozilla.org/show\_bug.cgi?id=1924932](https://bugzilla.mozilla.org/show_bug.cgi?id=1924932)  
45. DWM (Desktop Windows Manager) spikes GPU whenever I scroll or move browser tabs on Windows 11 \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/5592608/dwm-(desktop-windows-manager)-spikes-gpu-whenever](https://learn.microsoft.com/en-us/answers/questions/5592608/dwm-\(desktop-windows-manager\)-spikes-gpu-whenever)  
46. Desktop Window Manager (dwm.exe) High GPU usage on Windows 10/11 \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/answers/questions/4266403/desktop-window-manager-(dwm-exe)-high-gpu-usage-on](https://learn.microsoft.com/en-us/answers/questions/4266403/desktop-window-manager-\(dwm-exe\)-high-gpu-usage-on)  
47. WDDM Support for Timeout Detection and Recovery (TDR) \- Windows drivers, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/timeout-detection-and-recovery](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/timeout-detection-and-recovery)  
48. GPU drivers crash with long computations (TDR crash) | Substance ..., brukt februar 13, 2026, [https://helpx.adobe.com/substance-3d-painter/technical-support/technical-issues/gpu-issues/gpu-drivers-crash-with-long-computations-tdr-crash.html](https://helpx.adobe.com/substance-3d-painter/technical-support/technical-issues/gpu-issues/gpu-drivers-crash-with-long-computations-tdr-crash.html)  
49. Testing and Debugging TDR During Driver Development \- Microsoft Learn, brukt februar 13, 2026, [https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys)  
50. TdrDelay \= 10 Fixed my crashes since last patch. : r/battlefield\_4 \- Reddit, brukt februar 13, 2026, [https://www.reddit.com/r/battlefield\_4/comments/1xzzn4/tdrdelay\_10\_fixed\_my\_crashes\_since\_last\_patch/](https://www.reddit.com/r/battlefield_4/comments/1xzzn4/tdrdelay_10_fixed_my_crashes_since_last_patch/)