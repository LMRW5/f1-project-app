import React, { useState, useEffect } from "react";
import Footer from "./components/Footer.jsx";

const LATEST_ROUND = 14;
const CURR_SEASON = 2025;

export default function App() {
  const [upcomingRaces, setUpcomingRaces] = useState([]);
  const [selectedRace, setSelectedRace] = useState("");
  const [qualiPredictions, setQualiPredictions] = useState(null);
  const [racePredictions, setRacePredictions] = useState(null);
  const [driverImages, setDriverImages] = useState({});
  const [hoveredDriver, setHoveredDriver] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const [hoveredSection, setHoveredSection] = useState(null); // 'quali' or 'race'
  const [currRace, setCurrRace] = useState(null)
  const [driverPhotos, setDriverPhotos] = useState([]);

  useEffect(() => {
  if (currRace) {
    document.title = `F1 Predictions - ${currRace}`;
  } else {
    document.title = "F1 Prediction App";
  }
}, [currRace]);

  const getRowStyle = (pos) => {
    switch (pos) {
      case 1:
        return { backgroundColor: "#FFD70022" };
      case 2:
        return { backgroundColor: "#C0C0C022" };
      case 3:
        return { backgroundColor: "#CD7F3222" };
      default:
        return {};
    }
  };

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const isMobile = windowWidth < 768;

  // Fetch upcoming races
  useEffect(() => {
    const fetchUpcomingRaces = async () => {
      try {
        const res = await fetch("http://localhost:8000/Upcoming-Races", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ season: CURR_SEASON, round: LATEST_ROUND, race_name: "" }),
        });
        const data = await res.json();
        if (data.status === "ok" && data.upcoming.length > 0) {
          setUpcomingRaces(data.upcoming.map((r) => r.Name));
          setSelectedRace(data.upcoming[0].Name);
        } else {
          setError("No upcoming races found.");
        }
      } catch (err) {
        setError(err.message);
      }
    };
    fetchUpcomingRaces();
  }, []);

  const handleFetchPredictions = async () => {
    setLoading(true);
    setError(null);
    setQualiPredictions(null);
    setRacePredictions(null);
    setDriverImages({});

    try {
      const payload = {
        season: CURR_SEASON,
        round: LATEST_ROUND,
        race_name: selectedRace,
      };

      const [qualiRes, raceRes] = await Promise.all([
        fetch(`http://localhost:8000/predict-Quali`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`http://localhost:8000/predict-Race`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      ]);
      setCurrRace(selectedRace)
      const qualiData = await qualiRes.json();
      const raceData = await raceRes.json();

      if (qualiData.status === "ok") setQualiPredictions(qualiData.predictions);
      else setError(qualiData.message || "Error fetching qualifying predictions");

      if (raceData.status === "ok") setRacePredictions(raceData.predictions);
      else setError(raceData.message || "Error fetching race predictions");

      // Fetch driver images
    const imgRes = await fetch(`http://localhost:8000/Driver-Photos/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const imgData = await imgRes.json();

    // Store the full array so hover can use Color, etc.
    setDriverPhotos(imgData);

    const imgMap = {};
    imgData.forEach((d) => {
      imgMap[d.Driver] = d.Image !== "None" ? d.Image : null;
    });
    setDriverImages(imgMap);
  }catch(err){
    setError(err.message)
  } finally {
    setLoading(false)
  }};


  const tableStyle = {
    width: "100%",
    borderCollapse: "collapse",
    backgroundColor: "#1c1c1c",
    color: "#fff",
    borderRadius: "8px",
    overflow: "hidden",
  };

  const thStyle = {
    padding: "10px",
    backgroundColor: "#e10600",
    color: "#fff",
    fontWeight: "bold",
    textAlign: "left",
  };

  const tdStyle = {
    padding: "8px",
    borderBottom: "1px solid #333",
  };

    const renderTable = (title, predictions, section) => (
    <div style={{ flex: 1, margin: isMobile ? "10px 0" : "0 10px", minWidth: 0 }}>
      <h2 style={{ color: "#e10600", textAlign: "center" }}>{title}</h2>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>🏅 Pos</th>
            <th style={thStyle}>👤 Driver</th>
            <th style={thStyle}>⚡ Score</th>
            <th style={thStyle}>📊 Std Dev</th>
            <th style={thStyle}>🎯 Confidence</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map(({ Driver, Values }) => (
            <tr
              key={Driver}
              style={{
                ...getRowStyle(Values["Pos"]),
                transition: "background-color 0.3s ease",
                cursor: "pointer",
                backgroundColor:
                  hoveredDriver === Driver && hoveredSection === section
                    ? "rgba(255, 255, 255, 0.15)" // light highlight on hover
                    : getRowStyle(Values["Pos"]).backgroundColor || "transparent",
              }}
              onMouseMove={(e) => {
                setMousePos({ x: e.clientX, y: e.clientY });
              }}
              onMouseEnter={() => {
                setHoveredDriver(Driver);
                setHoveredSection(section);
              }}
              onMouseLeave={() => {
                setHoveredDriver(null);
                setHoveredSection(null);
              }}
            >
              <td style={tdStyle}>{Values["Pos"]}</td>
              <td style={tdStyle}>{Driver}</td>
              <td style={tdStyle}>{Values["Score"].toFixed(3)}</td>
              <td style={tdStyle}>{Values["Std Dev"].toFixed(3)}</td>
              <td style={tdStyle}>{(Values["Confidence"] * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );


  return (
  <div
    style={{
      minHeight: "100vh",
      backgroundColor: "#121212",
      fontFamily: "'Orbitron', sans-serif",
      display: "flex",
      flexDirection: "column",
      color: "#fff",
      position: "relative",
      width: "100vw",
      margin: 0,
      overflowX: "hidden" // prevents horizontal scrollbars
    }}
  >
{/* HEADER */}
<div
  style={{
    width: "100%",
    boxSizing: "border-box", // include padding in total width
    background: "linear-gradient(90deg, #1c1c1c, #2b2b2b)",
    borderBottom: "2px solid #e10600",
    padding: "20px",
    textAlign: "center",
    boxShadow: "0 4px 10px rgba(0,0,0,0.5)",
    overflowX: "hidden", // prevent accidental horizontal scroll from header
  }}
>
  <h1
    style={{
      color: "#e10600",
      fontSize: "3rem",
      margin: "0 0 15px 0",
      textShadow: "0px 0px 10px rgba(225,6,0,0.7)",
      overflowWrap: "break-word", // break long titles if needed
    }}
  >
    F1 Prediction App
  </h1>

  {/* Controls Row */}
  <div
    style={{
      display: "flex",
      flexWrap: "wrap", // wrap to next line on small screens
      justifyContent: "center",
      alignItems: "center",
      gap: "15px",
      marginBottom: "10px",
      maxWidth: "100%", // never exceed header width
      boxSizing: "border-box",
    }}
  >
    <label style={{ fontSize: "1.1rem", whiteSpace: "nowrap" }}>
      Select Race:
      <select
        value={selectedRace}
        onChange={(e) => setSelectedRace(e.target.value)}
        style={{
          marginLeft: 10,
          padding: "8px",
          backgroundColor: "#1c1c1c",
          color: "#fff",
          border: "1px solid #e10600",
          borderRadius: "4px",
          fontSize: "1rem",
          maxWidth: "200px", // prevent it from stretching too far
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {upcomingRaces.map((race) => (
          <option key={race} value={race}>
            {race}
          </option>
        ))}
      </select>
    </label>

    <button
      onClick={handleFetchPredictions}
      disabled={loading}
      style={{
        padding: "10px 20px",
        backgroundColor: "#e10600",
        color: "#fff",
        border: "none",
        borderRadius: "4px",
        cursor: "pointer",
        fontWeight: "bold",
        fontSize: "1rem",
        transition: "transform 0.15s ease, background-color 0.2s ease",
        whiteSpace: "nowrap", // keep button text in one line
      }}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
    >
      {loading ? "Loading..." : "Get Predictions"}
    </button>
  </div>

  {/* Error Message */}
  {error && (
    <div style={{ marginTop: 10, color: "#ff4d4d", fontWeight: "bold" }}>
      Error: {error}
    </div>
  )}

  {/* Subheader */}
  <div
    style={{
      marginTop: "8px",
      fontSize: "0.95rem",
      color: "#ccc",
      fontStyle: "italic",
      textAlign: "center",
      lineHeight: "1.4",
    }}
  >
    <div>
      Predicting results for{" "}
      <span style={{ color: "#fff" }}>
        <b>{currRace}</b>
      </span>
    </div>
    <div style={{ marginTop: "4px" }}>
      Using data from{" "}
      <span style={{ color: "#fff" }}>
        R{LATEST_ROUND} {CURR_SEASON}
      </span>
    </div>
  </div>
</div>

      {qualiPredictions && racePredictions && (
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginTop: "40px",
            width: "100%",
            padding: "0 20px",
            boxSizing: "border-box",
          }}
        >
          {renderTable("Qualifying Predictions", qualiPredictions, "quali")}
          {renderTable("Race Predictions", racePredictions, "race")}

        </div>
      )}

      {hoveredDriver && driverImages[hoveredDriver] && (() => {
  // Find driver object from driver photos API data
    const driverInfo = driverPhotos?.find(d => d.Driver === hoveredDriver);
    const driverColor = driverInfo ? `#${driverInfo.Color}` : "#e10600";
  return (
      <div
        style={{
          position: "fixed",
          top: mousePos.y + 15,
          left: mousePos.x + 15,
          backgroundColor: "#1c1c1c",
          border: `2px solid ${driverColor}`,
          borderRadius: "10px",
          padding: "10px",
          boxShadow: "0px 4px 15px rgba(0,0,0,0.6)",
          zIndex: 1000,
          pointerEvents: "none",
          width: "160px",
          textAlign: "center",
          transform: "scale(1)",
          transition: "transform 0.15s ease-in-out"
        }}
      >
        <img
          src={driverImages[hoveredDriver]}
          alt={hoveredDriver}
          style={{
            width: "100%",
            height: "auto",
            borderRadius: "8px",
            marginBottom: "8px"
          }}
        />
        <div style={{ fontSize: "1rem", fontWeight: "bold", color: "#fff", marginBottom: "6px" }}>
          {hoveredDriver}
        </div>
        <div style={{ fontSize: "0.9rem", color: "#ccc" }}>
          Pos: {
            hoveredSection === "quali"
              ? (qualiPredictions?.find(p => p.Driver === hoveredDriver)?.Values["Pos"] ?? "N/A")
              : hoveredSection === "race"
              ? (racePredictions?.find(p => p.Driver === hoveredDriver)?.Values["Pos"] ?? "N/A")
              : "N/A"
          }
        </div>
        <div style={{ fontSize: "0.9rem", color: "#ccc" }}>
          Confidence: {
            (() => {
              const conf = hoveredSection === "quali"
                ? qualiPredictions?.find(p => p.Driver === hoveredDriver)?.Values["Confidence"]
                : hoveredSection === "race"
                ? racePredictions?.find(p => p.Driver === hoveredDriver)?.Values["Confidence"]
                : null;

              return conf !== undefined && conf !== null
                ? (conf * 100).toFixed(2) + "%"
                : "N/A";
            })()
          }
        </div>
      </div>
    );
  })()}

      <Footer />
    </div>
  );
}
