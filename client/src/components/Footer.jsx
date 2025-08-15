import { FaTwitter, FaInstagram, FaGithub, FaEnvelope, FaLinkedin } from "react-icons/fa";
import React from "react";

const footerStyle = {
  backgroundColor: "#111", // slightly darker than main background (#121212)
  color: "#bbb",
  padding: "20px 40px",
  textAlign: "center",
  marginTop: "auto", // push footer to bottom if using flex layout in main container
  fontSize: "14px",
};

const iconStyle = {
  margin: "0 12px",
  color: "#bbb",
  cursor: "pointer",
  transition: "color 0.3s",
};

const iconHoverStyle = {
  color: "#e10600", // F1 red highlight on hover
};

export default function Footer() {
  const [hoveredIcon, setHoveredIcon] = React.useState(null);

  const socials = [
    { icon: <FaLinkedin />, link: "https://linkedin.com/in/ryan-wu88", label: "LinkedIn" },
    { icon: <FaInstagram />, link: "https://instagram.com/scuffed.game", label: "Instagram" },
    { icon: <FaGithub />, link: "https://github.com/LMRW5", label: "GitHub" },
  ];

  return (
    <footer style={footerStyle}>
      <div style={{ marginBottom: 8 }}>Connect with me:</div>
      <div>
        {socials.map(({ icon, link, label }, i) => (
          <a
            key={label}
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={label}
            style={{
              ...iconStyle,
              ...(hoveredIcon === i ? iconHoverStyle : {}),
              fontSize: "20px",
              display: "inline-block",
            }}
            onMouseEnter={() => setHoveredIcon(i)}
            onMouseLeave={() => setHoveredIcon(null)}
          >
            {icon}
          </a>
        ))}
      </div>
      <div style={{ marginTop: 12, fontSize: 12, color: "#666" }}>
        &copy; {new Date().getFullYear()} Ryan Wu. All rights reserved.
      </div>
    </footer>
  );
}
