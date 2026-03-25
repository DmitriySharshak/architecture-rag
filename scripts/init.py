import os
import json
import re
from pathlib import Path

class KnowledgeBaseGenerator:
    """Генератор уникальной базы знаний с заменой терминов"""
    
    def __init__(self, terms_map_file, output_dir="../knowledge_base"):
        with open(terms_map_file, 'r', encoding='utf-8') as f:
            self.terms_map = json.load(f)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Создаем единый словарь для замены
        self.replacement_dict = {}
        for category in self.terms_map:
            if category != "metadata":
                for original, new in self.terms_map[category].items():
                    self.replacement_dict[original] = new
        
        # Сортируем по длине для корректной замены (сначала длинные фразы)
        self.replacement_dict = dict(sorted(
            self.replacement_dict.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        ))
    
    def replace_terms(self, text):
        """Заменяет все термины в тексте согласно словарю"""
        for original, new in self.replacement_dict.items():
            # Используем границы слов для точной замены
            pattern = r'\b' + re.escape(original) + r'\b'
            text = re.sub(pattern, new, text)
        return text
    
    def create_document(self, title, content, filename):
        """Создает документ с замененными терминами"""
        # Заменяем термины в контенте
        transformed_content = self.replace_terms(content)
        
        # Сохраняем файл
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {self.replace_terms(title)}\n\n")
            f.write(transformed_content)
        
        return filepath
    
    def generate_star_wars_knowledge_base(self):
        """Генерирует базу знаний на основе Star Wars с заменой терминов"""
        
        documents = [
            # Основные персонажи
            ("Luke Skywalker", 
             """Luke Skywalker was a farm boy who became a legendary hero. He discovered his connection to the Force through 
             training with Master Obi-Wan Kenobi and later with Master Yoda. Luke wielded a blue lightsaber and later constructed 
             his own green blade. He played a crucial role in destroying the Death Star and redeeming his father, Anakin Skywalker, 
             from the dark side.""",
             "kaelen_vex.txt"),
            
            ("Darth Vader",
             """Darth Vader was a dark lord of the Sith, known for his black armor and mechanical breathing. Once a promising Jedi 
             named Anakin Skywalker, he fell to the dark side after being seduced by Emperor Palpatine. Vader served as the Emperor's 
             enforcer, commanding the Imperial fleet and hunting down Jedi survivors. Despite his evil reputation, he ultimately 
             redeemed himself by saving his son Luke from the Emperor.""",
             "xarn_velgor.txt"),
            
            ("Leia Organa",
             """Princess Leia Organa was a leader of the Rebel Alliance and a key figure in the fight against the Empire. She was a 
             skilled diplomat and military strategist who led from the front. Leia possessed a strong connection to the Force, though 
             she focused her efforts on political leadership. She was instrumental in obtaining the Death Star plans and establishing 
             the Alliance's base on Yavin 4.""",
             "seraphina_valoris.txt"),
            
            ("Han Solo",
             """Han Solo was a smuggler turned rebel hero. Captain of the Millennium Falcon, he and his co-pilot Chewbacca became 
             crucial allies to the Rebellion. Initially motivated by profit, Han developed a deep loyalty to the cause and to his 
             friends Luke and Leia. His quick thinking and piloting skills saved the day on numerous occasions.""",
             "jax_corvin.txt"),
            
            ("Obi-Wan Kenobi",
             """Obi-Wan Kenobi was a wise Jedi Master who trained both Anakin and Luke Skywalker. A general during the Clone Wars, 
             he was known for his mastery of the defensive lightsaber form Soresu. After the fall of the Republic, he lived in exile 
             on Tatooine, watching over young Luke. His sacrifice on the Death Star allowed the others to escape and made him more 
             powerful than Vader could imagine.""",
             "eldrin_thorne.txt"),
            
            ("Yoda",
             """Yoda was the Grand Master of the Jedi Order, known for his wisdom and powerful connection to the Force. Despite his 
             small stature, he was one of the greatest warriors and teachers in galactic history. After the rise of the Empire, Yoda 
             exiled himself to Dagobah, where he trained Luke Skywalker in the ways of the Force.""",
             "zephyr_nox.txt"),
            
            # Планеты
            ("Tatooine",
             """Tatooine is a desert planet orbiting binary stars. Covered in vast sand dunes and rocky wastes, it was home to 
             moisture farmers, criminals, and slaves. The planet's two suns made it a harsh environment where only the tough survived. 
             Key locations included Mos Eisley spaceport, known for its criminal elements, and the Lars family moisture farm where 
             Luke Skywalker grew up.""",
             "dusthal.txt"),
            
            ("Alderaan",
             """Alderaan was a peaceful planet known for its commitment to diplomacy and the arts. The homeworld of Princess Leia, 
             it served as a symbol of hope and culture in the galaxy. The planet was destroyed by the Death Star as a demonstration 
             of the Empire's power, an act that galvanized the Rebellion.""",
             "primara.txt"),
            
            ("Coruscant",
             """Coruscant served as the capital of the galaxy for millennia. An ecumenopolis—a city covering the entire planet—it 
             was the seat of political power, first for the Republic and later for the Empire. Its towering skylines housed trillions 
             of beings, while its lower levels were lawless and dangerous.""",
             "aetheria_prime.txt"),
            
            ("Hoth",
             """Hoth is a remote ice planet in the Outer Rim Territories. Covered in frozen wastelands and home to dangerous creatures 
             like wampas, it served as the site of the Rebel Alliance's Echo Base. The harsh conditions made it difficult for the 
             Empire to locate the base, but ultimately Imperial forces discovered it, leading to the evacuation at the Battle of Hoth.""",
             "glacius.txt"),
            
            ("Endor",
             """Endor is a forest moon known for its dense woodlands and primitive native species, the Ewoks. The Empire constructed 
             a second Death Star in orbit around Endor, with a shield generator located on the moon's surface. The Rebel Alliance's 
             strike team, with help from the Ewoks, destroyed the shield generator, allowing the fleet to destroy the battle station.""",
             "verdanis.txt"),
            
            # Технологии
            ("Death Star",
             """The Death Star was the Empire's ultimate weapon—a moon-sized battle station capable of destroying entire planets. 
             Armed with a superlaser powered by kyber crystals, it could fire a beam capable of annihilating any world. The first 
             Death Star was destroyed by Luke Skywalker's proton torpedo shot into a vulnerable exhaust port. A second, more powerful 
             version was later constructed but destroyed during the Battle of Endor.""",
             "void_core.txt"),
            
            ("Lightsaber",
             """The lightsaber is the signature weapon of the Jedi and Sith. It consists of a plasma blade powered by a kyber crystal, 
             contained within a energy field. The weapon requires a strong connection to the Force to construct and master. Colors 
             varied—blue and green for Jedi Knights, red for Sith who corrupted kyber crystals, and other rare colors for special 
             users. Each lightsaber was a personal weapon, uniquely constructed by its wielder.""",
             "phantom_blade.txt"),
            
            ("Millennium Falcon",
             """The Millennium Falcon was a modified YT-1300 freighter, famous for its speed and versatility. Under the ownership of 
             Han Solo and Chewbacca, it became a legendary ship in the Rebellion. Despite its beat-up appearance, the Falcon was 
             incredibly fast, with a powerful hyperdrive and extensive modifications. It made the Kessel Run in less than 12 parsecs 
             and played crucial roles in the destruction of both Death Stars.""",
             "shadow_runner.txt"),
            
            ("X-wing",
             """The X-wing starfighter was the primary starfighter of the Rebel Alliance. Its distinctive S-foils could open into 
             attack position, providing better weapons dispersion and cooling. Armed with four laser cannons and proton torpedoes, 
             the X-wing was versatile enough for both space combat and atmospheric operations. It was instrumental in the attack on 
             the Death Star.""",
             "striker_class_fighter.txt"),
            
            # Организации
            ("Jedi Order",
             """The Jedi Order was an ancient organization of Force-sensitive warriors who served as guardians of peace and justice 
             in the Republic. Guided by the principles of the light side, they practiced non-attachment, self-discipline, and service 
             to others. The Order was led by the Jedi Council and trained members from childhood. They were nearly exterminated by 
             Order 66, which labeled them enemies of the Empire.""",
             "order_of_the_aether.txt"),
            
            ("Sith",
             """The Sith were the ancient enemies of the Jedi, practitioners of the dark side of the Force. Their philosophy embraced 
             passion, power, and the overthrow of weakness. After centuries of conflict, the Sith adopted the Rule of Two: only two 
             Sith existed at any time—a master to embody power, and an apprentice to crave it. Darth Sidious and Darth Vader were the 
             last Sith lords before the Order's apparent destruction.""",
             "cult_of_the_void.txt"),
            
            ("Rebel Alliance",
             """The Rebel Alliance was a military coalition formed to oppose the Galactic Empire. Composed of defectors, planetary 
             defense forces, and freedom fighters, they fought against Imperial tyranny through guerrilla warfare and eventually 
             open battle. Their victory at Endor led to the Empire's defeat and the restoration of democracy to the galaxy.""",
             "free_dominion_coalition.txt"),
            
            ("Galactic Empire",
             """The Galactic Empire was the authoritarian government that replaced the Old Republic. Formed by Supreme Chancellor 
             Palpatine, who declared himself Emperor, the Empire maintained control through military force, fear, and the destruction 
             of dissent. It was characterized by humanocentrism, militarism, and the use of superweapons to intimidate worlds into 
             submission.""",
             "imperium_of_eternal_dominion.txt"),
            
            # Концепции
            ("The Force",
             """The Force is an energy field created by all living things that binds the galaxy together. It can be sensed and 
             manipulated by those with special training. The Force has two aspects—the light side, associated with selflessness and 
             harmony, and the dark side, associated with emotion and aggression. Jedi sought to serve the light side, while Sith 
             exploited the dark side for power.""",
             "synth_flux.txt"),
            
            ("Dark Side",
             """The dark side of the Force is the aspect accessed through strong emotions like fear, anger, and hatred. While it 
             offers quick power, it corrupts those who use it, leading to physical transformation and moral decay. The dark side 
             was embraced by the Sith and others seeking power without the discipline required by the light side.""",
             "void_corruption.txt")
        ]
        
        # Создаем все документы
        for title, content, filename in documents:
            self.create_document(title, content, filename)
            print(f"Created: {filename}")
        
        # Создаем дополнительные документы
        additional_docs = [
            ("Chewbacca", "Chewbacca was a Wookiee warrior and Han Solo's loyal co-pilot. Standing over two meters tall, he was a formidable fighter and a skilled mechanic. His loyalty to his friends was absolute, and he wielded a bowcaster with deadly accuracy. Chewbacca's life debt to Han bound them as brothers until the end.", "korr_varn.txt"),
            ("R2-D2", "R2-D2 was an astromech droid who served a crucial role in the Rebellion. With his small dome head and cylindrical body, he carried the Death Star plans that set Luke's journey in motion. Resourceful and brave beyond his programming, Artoo saved his companions countless times with his technical expertise.", "ar-7.txt"),
            ("C-3PO", "C-3PO was a protocol droid fluent in over six million forms of communication. Created by Anakin Skywalker, he served alongside R2-D2 throughout the galactic civil war. His fussy demeanor and constant concern for etiquette belied his deep loyalty to his friends.", "el-3x.txt"),
            ("Mustafar", "Mustafar was a volcanic planet wracked by constant seismic activity and rivers of molten lava. It was here that Anakin Skywalker fell to the dark side and was defeated by Obi-Wan Kenobi, resulting in his transformation into Darth Vader. The planet later served as a hiding place for Darth Vader's castle.", "infernus.txt"),
            ("Kamino", "Kamino was an ocean planet hidden beyond the outer rim. Its inhabitants, the Kaminoans, were master cloners who created the Grand Army of the Republic. The planet was removed from the Jedi archives to hide the cloning operations, making it nearly impossible to find without precise coordinates.", "aquaris.txt"),
            ("Blaster", "Blaster weapons fired bolts of charged plasma or particle energy. They came in many forms, from small hold-out pistols to heavy repeating rifles. While not as elegant as a lightsaber, blasters were reliable, easy to use, and could be deadly in skilled hands.", "ion_projector.txt"),
            ("Hyperdrive", "Hyperdrive technology allowed starships to travel faster than light by entering hyperspace. These drives required precise calculations to avoid gravity wells and could be classified by their speed rating—lower numbers meant faster travel. The Millennium Falcon's Class 0.5 hyperdrive was exceptionally fast.", "void_drive.txt"),
            ("Padawan", "A Padawan was a Jedi apprentice assigned to a Jedi Knight or Master for training. Padawans wore a distinctive braid to mark their status and were trained in lightsaber combat, Force abilities, and Jedi philosophy. Upon completing their trials, they could become Jedi Knights.", "initiate_of_the_aether.txt"),
            ("Star Destroyer", "Star Destroyers were wedge-shaped capital ships that served as the backbone of the Imperial Navy. Armed with turbolasers and carrying a full complement of TIE fighters, they projected Imperial power across the galaxy. The Executor-class Super Star Destroyer was a massive command ship over 19 kilometers long.", "oblivion_class_battleship.txt"),
            ("TIE Fighter", "TIE Fighters were the standard starfighters of the Imperial fleet. The twin ion engine design made them fast and maneuverable but fragile and lacking shields. TIE pilots were trained to rely on numbers and aggression to overwhelm their opponents.", "reaper_class_interceptor.txt")
        ]
        
        for title, content, filename in additional_docs:
            self.create_document(title, content, filename)
            print(f"Created: {filename}")
        
        print(f"\n✅ Total documents created: {len(documents) + len(additional_docs)}")
        
    def save_terms_map(self):
        """Сохраняет словарь замен"""
        with open(self.output_dir / "terms_map.json", 'w', encoding='utf-8') as f:
            json.dump(self.terms_map, f, ensure_ascii=False, indent=2)
        print("Saved terms_map.json")

# Запуск генерации
if __name__ == "__main__":
    # Создаем файл со словарем
    terms_map = {
        "metadata": {
            "original_universe": "Star Wars",
            "new_universe": "Nexus Dominion",
        },
        "characters": {
            "Luke Skywalker": "Kaelen Vex",
            "Darth Vader": "Xarn Velgor",
            "Leia Organa": "Seraphina Valoris",
            "Han Solo": "Jax Corvin",
            "Obi-Wan Kenobi": "Eldrin Thorne",
            "Yoda": "Zephyr Nox",
            "Palpatine": "Vorath Drakon",
            "Anakin Skywalker": "Damon Vex",
            "Chewbacca": "Korr Varn",
            "R2-D2": "AR-7",
            "C-3PO": "EL-3X",
            "Boba Fett": "Torin Kade"
        },
        "planets": {
            "Tatooine": "Dusthal",
            "Alderaan": "Primara",
            "Coruscant": "Aetheria Prime",
            "Hoth": "Glacius",
            "Endor": "Verdantis",
            "Dagobah": "Miremoor",
            "Mustafar": "Infernus",
            "Kamino": "Aquaris"
        },
        "technology_and_weapons": {
            "Death Star": "Void Core",
            "Lightsaber": "Phantom Blade",
            "X-wing": "Striker-class Fighter",
            "TIE Fighter": "Reaper-class Interceptor",
            "Star Destroyer": "Oblivion-class Battleship",
            "Millennium Falcon": "Shadow Runner",
            "Blaster": "Ion Projector",
            "Hyperdrive": "Void Drive",
            "Droid": "Synth Unit"
        },
        "organizations": {
            "Jedi Order": "Order of the Aether",
            "Sith": "Cult of the Void",
            "Rebel Alliance": "Free Dominion Coalition",
            "Galactic Empire": "Imperium of Eternal Dominion",
            "Republic": "Old Concordium"
        },
        "concepts": {
            "The Force": "Synth Flux",
            "Dark Side": "Void Corruption",
            "Light Side": "Aether Harmony",
            "Jedi Knight": "Aether Sentinel",
            "Sith Lord": "Void Reaver",
            "Padawan": "Initiate of the Aether",
            "Master": "Aether Lord"
        }
    }
    
    # Сохраняем terms_map.json отдельно
    with open("terms_map.json", 'w', encoding='utf-8') as f:
        json.dump(terms_map, f, ensure_ascii=False, indent=2)
    
    # Создаем базу знаний
    generator = KnowledgeBaseGenerator("terms_map.json")
    generator.generate_star_wars_knowledge_base()
    generator.save_terms_map()