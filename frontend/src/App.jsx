import { useEffect, useState } from "react";

import Login from "./Login";

import { api } from "./api";

import CustomerChat from "./CustomerChat";

import {

  Bot,

  LayoutDashboard,


  CalendarDays,


  Settings,

  Bell,

  Search,

  Plus,

  Clock,

  CheckCircle2,

  CalendarCheck,

  ArrowUpRight,

  Menu,

  X,


  Sparkles,

} from "lucide-react";



import "./App.css";



const navigation = [

  { label: "Dashboard", icon: LayoutDashboard },

  { label: "All Bookings", icon: CalendarDays },

  { label: "Settings", icon: Settings },

];





function getGreeting() {

  const hour = new Date().getHours();



  if (hour < 12) return "Good morning!";

  if (hour < 17) return "Good afternoon!";

  return "Good evening!";

}





function App() {

  const [token, setToken] = useState(() =>

    sessionStorage.getItem("access_token")

  );



  const [greeting, setGreeting] = useState(getGreeting);



  const [authLoading, setAuthLoading] = useState(true);

  const [authChecked, setAuthChecked] = useState(false);

  const [showAdminLogin, setShowAdminLogin] = useState(false);



  const [apiError, setApiError] = useState("");

  const [actionMessage, setActionMessage] = useState("");



  const [bookings, setBookings] = useState([]);

  const [pendingApprovals, setPendingApprovals] = useState([]);



  const [bookingsLoading, setBookingsLoading] = useState(false);

  const [approvalsLoading, setApprovalsLoading] = useState(false);



  const [processingApprovalId, setProcessingApprovalId] = useState(null);


  const [activePage, setActivePage] = useState("Dashboard");

  const [sidebarOpen, setSidebarOpen] = useState(false);




  const [searchTerm, setSearchTerm] = useState("");



  const appointments = bookings.map((booking) => {

    const start = new Date(booking.start_time);

    const end = new Date(booking.end_time);



    return {

      id: booking.id,

      name: booking.customer_name,

      email: booking.customer_email,

      service: "Appointment",

      date: start.toLocaleDateString(undefined, {

        month: "short",

        day: "numeric",

        year: "numeric",

      }),

      time: `${start.toLocaleTimeString([], {

        hour: "2-digit",

        minute: "2-digit",

      })} - ${end.toLocaleTimeString([], {

        hour: "2-digit",

        minute: "2-digit",

      })}`,

      status: booking.status,

      initials:

        booking.customer_name

          .split(/\s+/)

          .filter(Boolean)

          .map((part) => part[0])

          .join("")

          .slice(0, 2)

          .toUpperCase() || "?",

    };

  });


  // Include confirmed/database bookings and requests waiting for admin approval.
  const allBookingRecords = [
    ...appointments,
    ...pendingApprovals.map((approval) => ({
      id: `pending-${approval.approval_id}`,
      name: approval.customer_name || "Unknown customer",
      email: approval.customer_email || "No email provided",
      service: "Appointment request",
      date: "Awaiting approval",
      time: `Slot #${approval.slot_id ?? "N/A"}`,
      status: "pending",
      initials:
        approval.customer_name
          ?.split(/\s+/)
          .filter(Boolean)
          .map((part) => part[0])
          .join("")
          .slice(0, 2)
          .toUpperCase() || "?",
    })),
  ];

  const filteredAllBookings = allBookingRecords.filter((booking) =>
    `${booking.name} ${booking.email} ${booking.service} ${booking.status}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );



  const stats = [

    {

      label: "Total Booking Records",

      value: bookings.length,

      change: "From database",

      icon: CalendarCheck,

      color: "blue",

    },

    {

      label: "Pending Approvals",

      value: pendingApprovals.length,

      change: "Needs attention",

      icon: Clock,

      color: "orange",

    },

    {

      label: "Confirmed Bookings",

      value: bookings.filter(

        (booking) => booking.status === "confirmed"

      ).length,

      change: "From database",

      icon: CheckCircle2,

      color: "green",

    },

  ];



  useEffect(() => {

    const updateGreeting = () => setGreeting(getGreeting());



    updateGreeting();

    const intervalId = setInterval(updateGreeting, 60_000);



    return () => clearInterval(intervalId);

  }, []);





  async function refreshDashboard(accessToken = token) {

    if (!accessToken) return;



    setBookingsLoading(true);

    setApprovalsLoading(true);

    setApiError("");



    try {

      const [approvalResult, bookingResult] = await Promise.all([

        api.pendingApprovals(accessToken),

        api.getBookings(accessToken),

      ]);




      setPendingApprovals(approvalResult.approvals ?? []);



      setBookings(bookingResult.bookings ?? []);

    } catch (error) {

      if (

        error.message.includes("session is invalid") ||

        error.message.includes("401")

      ) {

        handleLogout();

      } else {

        setApiError(error.message || "Unable to load dashboard data.");

      }

    } finally {

      setBookingsLoading(false);

      setApprovalsLoading(false);

    }

  }



  useEffect(() => {

    let cancelled = false;



    async function loadDashboard() {

      if (!token) {

        setBookings([]);

        setPendingApprovals([]);

        setAuthLoading(false);

        setAuthChecked(true);

        return;

      }



      setAuthLoading(true);

      setBookingsLoading(true);

      setApprovalsLoading(true);

      setApiError("");



      try {

        const [approvalResult, bookingResult] = await Promise.all([

          api.pendingApprovals(token),

          api.getBookings(token),

        ]);



        if (!cancelled) {




          setPendingApprovals(approvalResult.approvals ?? []);

          setBookings(bookingResult.bookings ?? []);

        }

      } catch (error) {

        if (!cancelled) {

          if (

            error.message.includes("session is invalid") ||

            error.message.includes("401")

          ) {

            handleLogout();

          } else {

            setApiError(

              error.message || "Unable to load dashboard data."

            );

          }

        }

      } finally {

        if (!cancelled) {

          setAuthLoading(false);

          setAuthChecked(true);

          setBookingsLoading(false);

          setApprovalsLoading(false);

        }

      }

    }



    loadDashboard();



    return () => {

      cancelled = true;

    };

  }, [token]);



  async function handleLogin(credentials) {

    const result = await api.login(credentials);



    if (!result.access_token) {

      throw new Error("The server did not return an access token.");

    }



    sessionStorage.setItem("access_token", result.access_token);

    setApiError("");

    setToken(result.access_token);

    setAuthChecked(false);

  }



  function handleLogout() {

    sessionStorage.removeItem("access_token");



    setToken(null);

    setBookings([]);

    setPendingApprovals([]);

    setApiError("");

    setActionMessage("");

    setAuthChecked(false);

    setAuthLoading(false);

  }



  async function handleApproval(approvalId, action) {

    if (!token || processingApprovalId !== null) return;



    setProcessingApprovalId(approvalId);

    setApiError("");

    setActionMessage("");



    try {

      const result =

        action === "approve"

          ? await api.approveBooking(approvalId, token)

          : await api.rejectApproval(approvalId, token);



      setActionMessage(

        result.message ||

        (action === "approve"

          ? "Booking approved successfully."

          : "Approval request rejected.")

      );



      await refreshDashboard(token);

    } catch (error) {

      if (

        error.message.includes("session is invalid") ||

        error.message.includes("401")

      ) {

        handleLogout();

      } else {

        setApiError(error.message || "Unable to process the request.");

      }

    } finally {

      setProcessingApprovalId(null);

    }

  }

  function renderDashboard() {

    return (

      <>

        <section className="welcome-section">

          <div>

            <div className="eyebrow">

              <Sparkles size={15} />

              YOUR WORKSPACE

            </div>



            <h2>{greeting}</h2>



            <p>

              Here's what's happening with your appointments today.

            </p>

          </div>



          <button

            className="primary-button"

            onClick={() => setActivePage("All Bookings")}

          >

            <Plus size={18} />

            View bookings

          </button>

        </section>



        {apiError && (

          <div className="error-message" role="alert">

            {apiError}

          </div>

        )}



        {actionMessage && (

          <div className="success-message" role="status">

            {actionMessage}

          </div>

        )}



        {bookingsLoading && (

          <p className="muted-text">Loading appointments...</p>

        )}



        <section className="stats-grid">

          {stats.map((stat) => {

            const Icon = stat.icon;



            return (

              <article className="stat-card" key={stat.label}>

                <div className="stat-top">

                  <span className="stat-label">{stat.label}</span>



                  <span className={`stat-icon ${stat.color}`}>

                    <Icon size={20} />

                  </span>

                </div>



                <div className="stat-bottom">

                  <h3>{stat.value}</h3>



                  <span className={`stat-change ${stat.color}`}>

                    {stat.change}

                  </span>

                </div>

              </article>

            );

          })}

        </section>



        <section className="dashboard-grid">

          <article className="panel appointments-panel">

            <div className="panel-heading">

              <div>

                <h3>Recent appointments</h3>

                <p>Keep track of your latest bookings.</p>

              </div>



              <button

                className="text-button"

                onClick={() => setActivePage("All Bookings")}

              >

                View all <ArrowUpRight size={16} />

              </button>

            </div>



            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>

                    <th>Customer</th>

                    <th>Service</th>

                    <th>Date & time</th>

                    <th>Status</th>

                  </tr>

                </thead>



                <tbody>

                  {appointments.slice(0, 4).map((appointment) => (

                    <tr key={appointment.id}>

                      <td>

                        <div className="customer-cell">

                          <span className="avatar">

                            {appointment.initials}

                          </span>



                          <div>

                            <strong>{appointment.name}</strong>

                            <small>{appointment.email}</small>

                          </div>

                        </div>

                      </td>



                      <td>{appointment.service}</td>



                      <td>

                        <div className="date-cell">

                          <strong>{appointment.date}</strong>

                          <small>{appointment.time}</small>

                        </div>

                      </td>



                      <td>

                        <span

                          className={`status-badge ${appointment.status.toLowerCase()}`}

                        >

                          {appointment.status}

                        </span>

                      </td>

                    </tr>

                  ))}



                  {!bookingsLoading && appointments.length === 0 && (

                    <tr>

                      <td colSpan="4">

                        No booking records found.

                      </td>

                    </tr>

                  )}

                </tbody>

              </table>

            </div>

          </article>





        </section>



        <section className="panel page-panel">

          <div className="panel-heading">

            <div>

              <h3>Pending approvals</h3>

              <p>Review booking requests before confirming them.</p>

            </div>



            <span className="total-count">

              {pendingApprovals.length} pending

            </span>

          </div>



          {approvalsLoading && (

            <p className="muted-text">Loading approval requests...</p>

          )}



          {!approvalsLoading && pendingApprovals.length === 0 && (

            <p className="muted-text">

              No pending approval requests.

            </p>

          )}



          <div className="appointment-list">

            {pendingApprovals.map((approval) => (

              <article

                className="appointment-card"

                key={approval.approval_id}

              >

                <div className="appointment-card-main">

                  <span className="avatar large">

                    {approval.customer_name

                      ?.split(/\s+/)

                      .filter(Boolean)

                      .map((part) => part[0])

                      .join("")

                      .slice(0, 2)

                      .toUpperCase() || "?"}

                  </span>



                  <div className="approval-customer">

                    <h4>{approval.customer_name}</h4>

                    <p>{approval.customer_email}</p>



                    <div className="service-label">

                      <span>Approval request #{approval.approval_id}</span>

                      <hr />

                      <span>Slot ID #{approval.slot_id}</span>

                    </div>

                  </div>

                </div>



                <div className="appointment-actions">

                  <span className="status-badge pending">

                    Pending

                  </span>



                  <button

                    className="approve-button"

                    disabled={processingApprovalId !== null}

                    onClick={() =>

                      handleApproval(approval.approval_id, "approve")

                    }

                  >

                    <CheckCircle2 size={16} />

                    {processingApprovalId === approval.approval_id

                      ? "Processing..."

                      : "Approve"}

                  </button>



                  <button

                    className="text-button"

                    disabled={processingApprovalId !== null}

                    onClick={() =>

                      handleApproval(approval.approval_id, "reject")

                    }

                  >

                    Reject

                  </button>

                </div>



              </article>

            ))}

          </div>

        </section>

      </>

    );

  }





  function renderAppointments() {

    return (

      <section className="panel page-panel">

        <div className="panel-heading">

          <div>

            <h3>All Bookings</h3>

            <p>View and search all appointment booking records.</p>

          </div>



          <span className="total-count">

            {filteredAllBookings.length} bookings

          </span>

        </div>



        {apiError && (

          <div className="error-message" role="alert">

            {apiError}

          </div>

        )}



        {(bookingsLoading || approvalsLoading) && (

          <p className="muted-text">Loading booking records...</p>

        )}



        <div className="search-box appointment-search">

          <Search size={18} />



          <input

            value={searchTerm}

            onChange={(event) => setSearchTerm(event.target.value)}

            placeholder="Search by customer name or email..."

          />

        </div>



        <div className="appointment-list">

          {filteredAllBookings.map((appointment) => (

            <article

              className="appointment-card"

              key={appointment.id}

            >

              <div className="appointment-card-main">

                <span className="avatar large">

                  {appointment.initials}

                </span>



                <div>

                  <h4>{appointment.name}</h4>

                  <p>{appointment.email}</p>



                  <span className="service-label">

                    {appointment.service}

                  </span>

                </div>

              </div>



              <div className="appointment-time">

                <CalendarDays size={17} />



                <div>

                  <strong>{appointment.date}</strong>

                  <span>{appointment.time}</span>

                </div>

              </div>



              <div className="appointment-actions">

                <span

                  className={`status-badge ${appointment.status.toLowerCase()}`}

                >

                  {appointment.status}

                </span>

              </div>

            </article>

          ))}



          {!bookingsLoading && !approvalsLoading && filteredAllBookings.length === 0 && (

            <div className="empty-state">

              <CalendarDays size={30} />

              <h4>No bookings found</h4>

              <p>Try searching with a different customer name or email.</p>

            </div>

          )}

        </div>

      </section>

    );

  }

  function renderPage() {

    switch (activePage) {



      case "All Bookings":

        return renderAppointments();



      case "Settings":

        return (

          <section className="panel page-panel">

            <h3>Settings</h3>

            <p className="muted-text">

              Application settings will be available here.

            </p>

          </section>

        );



      default:

        return renderDashboard();

    }

  }



  if (authLoading && !authChecked) {

    return (

      <main className="login-page">

        <p>Checking your session...</p>

      </main>

    );

  }



  if (!authChecked || authLoading) {

    return (

      <main className="login-page">

        <p>Checking your session...</p>

      </main>

    );

  }



  if (!token && showAdminLogin) {

    return (

      <div className="admin-login-screen">

        <button

          type="button"

          className="back-to-chat-button"

          onClick={() => setShowAdminLogin(false)}

        >

          ← Back to AI Receptionist

        </button>



        <Login onLogin={handleLogin} />

      </div>

    );

  }



  if (!token) {

    return (

      <CustomerChat

        onAdminLoginClick={() => setShowAdminLogin(true)}

      />

    );

  }



  return (

    <div className="app-shell">

      {sidebarOpen && (

        <button

          className="mobile-overlay"

          aria-label="Close navigation"

          onClick={() => setSidebarOpen(false)}

        />

      )}



      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>

        <div className="brand">

          <div className="brand-icon">

            <Bot size={25} />

          </div>



          <div className="brand-copy">

            <h1>ReceptionAI</h1>

            <span>INTELLIGENT ASSISTANT</span>

          </div>



          <button

            className="mobile-close"

            onClick={() => setSidebarOpen(false)}

            aria-label="Close sidebar"

          >

            <X size={20} />

          </button>

        </div>



        <div className="workspace-label">WORKSPACE</div>



        <nav className="navigation">

          {navigation.map((item) => {

            const Icon = item.icon;



            return (

              <button

                key={item.label}

                className={`nav-item ${activePage === item.label ? "active" : ""

                  }`}

                onClick={() => {

                  setActivePage(item.label);

                  setSidebarOpen(false);

                }}

              >

                <Icon size={19} strokeWidth={1.8} />



                <span>{item.label}</span>



                {item.label === "All Bookings" && (

                  <span className="nav-count">

                    {bookings.length}

                  </span>

                )}

              </button>

            );

          })}

        </nav>



        <div className="sidebar-bottom">

          <div className="upgrade-card">

            <div className="upgrade-icon">

              <Sparkles size={19} />

            </div>



            <h4>AI-powered service</h4>

            <p>Smarter conversations. Easier scheduling.</p>

          </div>



          <div className="profile">

            <div className="profile-avatar">AR</div>



            <div className="profile-info">

              <strong>Administrator</strong>

              <span>Workspace preview</span>

            </div>



            <Settings size={17} className="profile-settings" />

          </div>

        </div>

      </aside>



      <main className="main-area">

        <header className="topbar">

          <div className="topbar-left">

            <button

              className="mobile-menu"

              onClick={() => setSidebarOpen(true)}

              aria-label="Open navigation"

            >

              <Menu size={22} />

            </button>



            <div className="breadcrumb">

              <span>Workspace</span>

              <span className="breadcrumb-separator">/</span>

              <strong>{activePage}</strong>

            </div>

          </div>



          <div className="topbar-actions">

            <label className="search-box global-search">

              <Search size={17} />

              <input placeholder="Search..." aria-label="Search" />

              <kbd>⌘ K</kbd>

            </label>



            <button

              className="icon-button notification-button"

              aria-label="Notifications"

            >

              <Bell size={19} />

              <span />

            </button>



            <div className="topbar-divider" />



            <div className="topbar-profile">

              <div className="profile-avatar">AR</div>



              <div>

                <strong>Admin</strong>

                <span>Administrator</span>

              </div>

            </div>



            <button className="primary-button" onClick={handleLogout}>

              Sign out

            </button>

          </div>

        </header>



        <div className="page-content">

          {renderPage()}



          <footer className="footer">

            <span>© 2026 ReceptionAI</span>

            <span>AI-powered appointment management</span>

          </footer>

        </div>

      </main>

    </div>

  );

}



export default App;
