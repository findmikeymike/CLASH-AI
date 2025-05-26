import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

interface Character {
  id: string;
  name: string;
  description: string;
  expertise: string[];
  avatarUrl: string;
}

interface CharacterGridProps {
  characters?: Character[];
  onCharacterSelect?: (character: Character) => void;
}

const CharacterGrid = ({
  characters = defaultCharacters,
  onCharacterSelect = () => {},
}: CharacterGridProps) => {
  const [hoveredCharacterId, setHoveredCharacterId] = useState<string | null>(
    null,
  );

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-6 relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <div className="absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-10"></div>
      </div>

      <div className="relative z-10">
        <div className="mb-16 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center space-y-6"
          >
            <h2 className="text-5xl md:text-7xl font-bold tracking-tight text-white">
              Choose Your
              <span className="block text-red-500 font-black">Opponent</span>
            </h2>
            <p className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Select an AI character and engage in intelligent debate
            </p>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 md:gap-8">
          {characters.map((character) => (
            <motion.div
              key={character.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              whileHover={{ scale: 1.05, y: -5 }}
              whileTap={{ scale: 0.98 }}
              onMouseEnter={() => setHoveredCharacterId(character.id)}
              onMouseLeave={() => setHoveredCharacterId(null)}
              onClick={() => onCharacterSelect(character)}
            >
              <Card className="h-full cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-xl bg-gradient-to-br from-gray-900 to-black border border-gray-800 hover:border-red-500/50 shadow-lg relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <CardContent className="p-0 relative z-10">
                  <div className="relative h-64 overflow-hidden">
                    <Avatar className="w-full h-full rounded-none">
                      <AvatarImage
                        src={character.avatarUrl}
                        alt={character.name}
                        className="object-cover w-full h-full"
                        style={{ objectPosition: "center 20%" }}
                      />
                      <AvatarFallback className="w-full h-full text-2xl bg-gray-800 text-white">
                        {character.name.substring(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    {hoveredCharacterId === character.id && (
                      <div className="absolute inset-0 bg-gradient-to-br from-black/90 to-gray-900/90 backdrop-blur-sm flex items-center justify-center">
                        <div className="relative group">
                          <div className="absolute -inset-0.5 bg-gradient-to-r from-red-600 to-red-500 rounded-lg blur opacity-70 animate-pulse"></div>
                          <span className="relative flex items-center justify-center text-white font-bold px-6 py-3 rounded-lg bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 transition-all duration-300 border border-red-700/50">
                            START DEBATE
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="p-5">
                    <h3 className="font-bold text-lg mb-2 text-white">
                      {character.name}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                      {character.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {character.expertise.slice(0, 2).map((skill, index) => (
                        <Badge
                          key={index}
                          variant="secondary"
                          className="text-xs bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        >
                          {skill}
                        </Badge>
                      ))}
                      {character.expertise.length > 2 && (
                        <Badge
                          variant="outline"
                          className="text-xs border-gray-600 text-gray-400"
                        >
                          +{character.expertise.length - 2} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Default characters for development and testing
const defaultCharacters: Character[] = [
  {
    id: "1",
    name: "Caleb the Feisty Liberal",
    description:
      "A passionate progressive advocate with strong opinions on social justice, climate action, and economic equality.",
    expertise: [
      "Social Justice",
      "Climate Policy",
      "Progressive Politics",
      "Economic Equality",
    ],
    avatarUrl: "/caleb.png",
  },
  {
    id: "9",
    name: "Tom the American Conservative",
    description:
      "Traditional conservative voice advocating for constitutional principles, free markets, and American values.",
    expertise: [
      "Constitutional Law",
      "Free Market Economics",
      "Traditional Values",
      "American History",
    ],
    avatarUrl: "/tom.png",
  },
  {
    id: "10",
    name: "Zeek the Nihilist",
    description:
      "A philosophical nihilist who questions the meaning and value of everything, challenging conventional beliefs and assumptions.",
    expertise: [
      "Philosophy",
      "Existentialism",
      "Critical Thinking",
      "Deconstruction",
    ],
    avatarUrl: "/Zeek.png",
  },
  {
    id: "12",
    name: "Sarah the Hippy",
    description:
      "A free-spirited advocate for peace, love, and environmental consciousness who believes in holistic living and spiritual awakening.",
    expertise: [
      "Environmental Activism",
      "Holistic Health",
      "Spirituality",
      "Peace Movement",
    ],
    avatarUrl: "/sarah.png",
  },
  {
    id: "11",
    name: "Chad the Alpha",
    description:
      "A confident alpha personality who believes in traditional masculinity, self-improvement, and taking charge in any situation.",
    expertise: [
      "Leadership",
      "Fitness",
      "Confidence Building",
      "Traditional Masculinity",
    ],
    avatarUrl: "/chad.png",
  },
  {
    id: "13",
    name: "Karen from Facebook",
    description:
      "A passionate social media activist who speaks her mind about community issues and isn't afraid to ask for the manager.",
    expertise: [
      "Social Media",
      "Community Advocacy",
      "Consumer Rights",
      "Local Politics",
    ],
    avatarUrl: "/karen.png",
  },
  {
    id: "16",
    name: "Lexi the Liberated",
    description:
      "A free-thinking feminist who challenges traditional gender roles and advocates for personal empowerment and social liberation.",
    expertise: [
      "Feminism",
      "Gender Studies",
      "Social Liberation",
      "Personal Empowerment",
    ],
    avatarUrl: "/lexi.png",
  },
  {
    id: "15",
    name: "Father Augustine",
    description:
      "A wise and contemplative priest who brings theological wisdom and moral philosophy to debates about faith, ethics, and the human condition.",
    expertise: ["Theology", "Moral Philosophy", "Ethics", "Spiritual Guidance"],
    avatarUrl: "/augustine.png",
  },
  {
    id: "17",
    name: "Professor Beckley",
    description:
      "A distinguished academic and policy expert who brings scholarly rigor and analytical thinking to complex political and social issues.",
    expertise: [
      "Political Science",
      "Policy Analysis",
      "Academic Research",
      "Public Administration",
    ],
    avatarUrl: "/beckley.png",
  },
  {
    id: "14",
    name: "Theo the Tech Futurist",
    description:
      "A visionary technologist who believes in the transformative power of AI, blockchain, and emerging technologies to solve humanity's greatest challenges.",
    expertise: [
      "Artificial Intelligence",
      "Blockchain Technology",
      "Future Tech",
      "Digital Innovation",
    ],
    avatarUrl: "/theo.png",
  },
];

export default CharacterGrid;
