import React, { useState, useEffect } from "react";
import Footer from "./components/Footer.jsx";

const IP = "localhost"
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
        const res = await fetch(`http://${IP}:8000/Upcoming-Races`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ season: CURR_SEASON, round: LATEST_ROUND, race_name: "" }),
        });
        const data = await res.json();
        if (data.status === "ok" && data.upcoming.length > 0) {
          setUpcomingRaces(data.upcoming.map((r) => r.Name));
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
        fetch(`http://${IP}:8000/predict-Quali`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`http://${IP}:8000/predict-Race`, {
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
      const imgRes = await fetch(`http://${IP}:8000/Driver-Photos/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const imgData = await imgRes.json();
      console.log(imgData)

      // Store the full array so hover can use Color, etc.
      setDriverPhotos(imgData);


      const imgMap = {};
      imgData.forEach((d) => {
        imgMap[d.Driver] = d.Image !== "None" ? d.Image : null;
      });
      setDriverImages(imgMap);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tableStyle = {
    width: "100%",       // take all available space in flex item
    borderCollapse: "collapse",
    backgroundColor: "#2c2c2c",
    color: "#fff",
    borderRadius: "8px",
    overflow: "hidden",
    boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
  };


  const thStyle = {
    padding: isMobile ? "8px" : "12px",
    backgroundColor: "#e10600",
    color: "#fff",
    fontWeight: "bold",
    textAlign: "left",
    borderBottom: "2px solid #fff",
  };

  const tdStyle = {
    padding: isMobile ? "8px" : "12px",
    borderBottom: "1px solid #333",
    textAlign: "center",
  };
  
  const renderTable = (title, predictions, section) => {
  // Skip the top 3 drivers (positions 1, 2, and 3)
  const restDrivers = predictions.filter(({ Values }) => Values["Pos"] > 3);

  return (
    <div 
      style={{ 
        flex: 1, 
        margin: isMobile ? "10px 0" : "0 10px", 
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center"
      }}
    >
      <h2 style={{ color: "#e10600", textAlign: "center" }}>{title}</h2>
      <Podium predictions={predictions}  section={section} />
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
          {restDrivers.map(({ Driver, Values }) => (
            <tr
              key={Driver}
              style={{
                ...getRowStyle(Values["Pos"]),
                transition: "background-color 0.3s ease",
                cursor: "pointer",
                backgroundColor:
                  hoveredDriver === Driver && hoveredSection === section
                    ? "rgba(255, 255, 255, 0.1)"
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
};
    // Estimate popup dimensions
  const popupWidth = isMobile ? 120 : 160;
  const popupHeight = isMobile ? 180 : 220;

  // Get viewport size
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // Default popup position (near mouse)
  let popupTop = mousePos.y + 15;
  let popupLeft = mousePos.x + 15;

  // Adjust vertical position if popup goes below viewport
  if (popupTop + popupHeight > viewportHeight) {
    popupTop = mousePos.y - popupHeight - 15;
    if (popupTop < 0) popupTop = 0;
  }

  // Adjust horizontal position if popup goes beyond right edge
  if (popupLeft + popupWidth > viewportWidth) {
    popupLeft = mousePos.x - popupWidth - 15;
    if (popupLeft < 0) popupLeft = 0;
  }
  // Find the index of the selected race in upcomingRaces
  const selectedRaceIndex = upcomingRaces.indexOf(selectedRace);

  // Get driver color once here too
  const driverInfo = hoveredDriver ? driverPhotos?.find(d => d.Driver === hoveredDriver) : null;
  const driverColor = driverInfo ? `#${driverInfo.Color}` : "#e10600";
  function Podium({ predictions, section }) {
    if (!predictions || predictions.length < 3) return null;

    const top3 = predictions.slice(0, 3);
    const podiumHeights = isMobile ? [140, 120, 100] : [200, 160, 140];

    // Helper to get last name from full driver name
    const getLastName = (fullName) => {
      const parts = fullName.trim().split(" ");
      return parts[parts.length - 1];
    };

    return (
      <>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "flex-end",
            gap: "20px",
            marginTop: "40px",
          }}
        >
          {top3.map(({ Driver }, i) => {
            const isHovered = hoveredDriver === Driver && hoveredSection === section;
            return (
              <div
                key={Driver}
                style={{
                  width: isMobile ? "80px" : "130px",
                  height: podiumHeights[i],
                  backgroundColor: isHovered
                    ? "rgba(255, 255, 255, 0.2)"
                    : i === 0
                    ? "#FFD700"
                    : i === 1
                    ? "#C0C0C0"
                    : "#CD7F32",
                  borderRadius: "8px 8px 0 0",
                  boxShadow: "0 3px 7px rgba(0,0,0,0.4)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "flex-start",
                  padding: "10px 8px",
                  color: "#121212",
                  fontWeight: "bold",
                  textAlign: "center",
                  overflow: "hidden",
                  cursor: "pointer",
                  transition: "background-color 0.3s ease",
                }}
                onMouseEnter={() => {
                  setHoveredDriver(Driver);
                  setHoveredSection(section);
                }}
                onMouseLeave={() => {
                  setHoveredDriver(null);
                  setHoveredSection(null);
                }}
                onMouseMove={(e) => {
                  setMousePos({ x: e.clientX, y: e.clientY });
                }}
              >
                {driverImages[Driver] ? (
                  <img
                    src={driverImages[Driver]}
                    alt={Driver}
                    style={{
                      width: "100%",
                      maxHeight: podiumHeights[i] - 40, // a bit more room for name
                      objectFit: "contain",
                      borderRadius: "6px",
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: "100%",
                      height: podiumHeights[i] - 40,
                      backgroundColor: "#444",
                      borderRadius: "6px",
                    }}
                  />
                )}
                {/* Last name under the image */}
                <div style={{ marginTop: "10px", fontSize: "1.3rem", whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden", width: "100%" }}>
                  {getLastName(Driver)}
                </div>
              </div>
            );
          })}
        </div>
      </>
    );
  }


    return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#121212",
        fontFamily: "'Roboto', sans-serif",
        display: "flex",
        flexDirection: "column",
        color: "#fff",
        position: "relative",
        width: "100%",
        margin: 0,
        overflowX: "hidden",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          width: "100%",
          boxSizing: "border-box",
          background: "linear-gradient(90deg, #1c1c1c, #2b2b2b)",
          borderBottom: "2px solid #e10600",
          padding: "20px",
          textAlign: "center",
          boxShadow: "0 4px 10px rgba(0,0,0,0.5)",
          overflowX: "hidden",
        }}
      >
        <h1
          style={{
            color: "#e10600",
            fontSize: isMobile ? "2rem" : "3rem",
            margin: "0 0 15px 0",
            textShadow: "0px 0px 10px rgba(225,6,0,0.7)",
            overflowWrap: "break-word",
          }}
        >
          F1 Prediction App
        </h1>

        {/* Controls Row */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            alignItems: "center",
            gap: "15px",
            marginBottom: "10px",
            maxWidth: "100%",
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
              maxWidth: "200px",
              overflow: "hidden",
            }}
          >
            <option value="" disabled>
              Choose A Grand Prix
            </option>
            {upcomingRaces.map((race) => (
              <option key={race} value={race}>
                {race}
              </option>
            ))}
          </select>
          </label>

          <button
            onClick={handleFetchPredictions}
            disabled={loading | !selectedRace}
            style={{
              padding: "10px 20px",
              backgroundColor: selectedRace ? "#e10600": "hsla(2, 100%, 17%, 0.6)" ,
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "1rem",
              transition: "transform 0.15s ease, background-color 0.2s ease",
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
            Currently predicting results for{" "}
            <span style={{ color: "#fff" }}>
              <b>{currRace ? currRace: "None"}</b>
            </span>
          </div>
          <div style={{ marginTop: "4px" }}>
            Using data from{" "}
            <span style={{ color: "#fff" }}>
              R{LATEST_ROUND} {CURR_SEASON}
            </span>
          </div>
          {selectedRaceIndex > 0 && (
          <div
            style={{
              marginTop: "12px",
              padding: "10px",
              backgroundColor: "#ff4d4d",
              color: "#fff",
              borderRadius: "6px",
              fontWeight: "bold",
              textAlign: "center",
              maxWidth: "600px",
              marginLeft: "auto",
              marginRight: "auto",
              boxShadow: "0 2px 8px rgba(255, 77, 77, 0.6)",
            }}
          >
            ⚠️ Warning: You are predicting more than one race ahead. Results may be less accurate!
          </div>
        )}
        </div>
        
      </div>
      


      {qualiPredictions && racePredictions && (
  <div
    style={{
      display: "flex",
      flexDirection: isMobile ? "column" : "row",
      justifyContent: "center", // center tables horizontally
      alignItems: "flex-start",
      gap: "20px", // space between tables
      marginTop: "40px",
      width: "100%",
      maxWidth: "100%",
      padding: isMobile ? "0 10px" : "0 20px",
      boxSizing: "border-box",
      overflowX: "hidden", // prevent accidental scroll
      flexWrap: "wrap", // wrap on small screens
    }}
  >
    <div style={{ flex: "1 1 400px", minWidth: "320px" }}>
      {renderTable("⏱️Qualifying Predictions", qualiPredictions, "quali")}
      
    </div>
    <div style={{ flex: "1 1 400px", minWidth: "320px" }}>
      {renderTable("🏁Race Predictions", racePredictions, "race")}
    </div>
  </div>
)}

      {hoveredDriver && driverImages[hoveredDriver] && (
      <div
        style={{
          position: "fixed",
          top: popupTop,
          left: popupLeft,
          backgroundColor: "#1c1c1c",
          border: `2px solid ${driverColor}`,
          borderRadius: "10px",
          padding: "10px",
          boxShadow: "0px 4px 15px rgba(0,0,0,0.6)",
          zIndex: 1000,
          pointerEvents: "none",
          width: `${popupWidth}px`,
          textAlign: "center",
          transform: "scale(1)",
          transition: "transform 0.15s ease-in-out",
        }}
      >
        <img
          src={driverImages[hoveredDriver]}
          alt={hoveredDriver}
          style={{
            width: "100%",
            height: "auto",
            borderRadius: "8px",
            marginBottom: "8px",
          }}
        />
        <div style={{ fontSize: "1rem", fontWeight: "bold", color: "#fff", marginBottom: "0px" }}>
          {hoveredDriver}
        </div>
        <div style={{ fontSize: "0.9rem", color: driverColor, marginBottom: "6px" }}>
        {driverInfo?.Team ?? "Unknown Team"}
        </div>
        <div style={{ fontSize: "0.9rem", color: "#ccc" }}>
          Pos: {hoveredSection === "quali"
            ? (qualiPredictions?.find(p => p.Driver === hoveredDriver)?.Values["Pos"] ?? "N/A")
            : hoveredSection === "race"
              ? (racePredictions?.find(p => p.Driver === hoveredDriver)?.Values["Pos"] ?? "N/A")
              : "N/A"}
        </div>
                 <div style={{ fontSize: "0.9rem", color: "#ccc" }}>
          Std Dev: {
            (() => {
              const conf = hoveredSection === "quali"
                ? qualiPredictions?.find(p => p.Driver === hoveredDriver)?.Values["Std Dev"]
                : hoveredSection === "race"
                  ? racePredictions?.find(p => p.Driver === hoveredDriver)?.Values["Std Dev"]
                  : null;

              return conf !== undefined && conf !== null
                ? (conf).toFixed(2)
                : "N/A";
            })()
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
    )}

      <Footer />
    </div>
  );
}
