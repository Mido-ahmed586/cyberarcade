import { createContext, useContext, useState } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedLab, setSelectedLab] = useState(null);

  return (
    <AppContext.Provider
      value={{
        chatOpen,
        setChatOpen,
        selectedCourse,
        setSelectedCourse,
        selectedLab,
        setSelectedLab,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  return useContext(AppContext);
}
