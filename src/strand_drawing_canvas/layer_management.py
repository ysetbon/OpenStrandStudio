import logging
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer
from strand import Strand, AttachedStrand, MaskedStrand

class LayerManagementMixin:
    def set_layer_panel(self, layer_panel):
        self.layer_panel = layer_panel
        self.layer_panel.draw_names_requested.connect(self.toggle_name_drawing)

    def toggle_name_drawing(self, should_draw):
        self.should_draw_names = should_draw
        self.update()

    def enable_name_drawing(self):
        self.should_draw_names = True
        self.update()

    def deselect_all_strands(self):
        self.selected_strand = None
        self.selected_strand_index = None
        self.update()

    def update_color_for_set(self, set_number, color):
        logging.info(f"Updating color for set {set_number} to {color.name()}")
        self.strand_colors[set_number] = color
        for strand in self.strands:
            if isinstance(strand, MaskedStrand):
                mask_parts = strand.layer_name.split('_')
                if mask_parts[0] == str(set_number):
                    strand.set_color(color)
                    logging.info(f"Updated color for masked strand: {strand.layer_name}")
            elif isinstance(strand, Strand):
                if strand.set_number == set_number:
                    strand.set_color(color)
                    logging.info(f"Updated color for strand: {strand.layer_name}")
                    self.update_attached_strands_color(strand, color)
        self.update()
        logging.info(f"Finished updating color for set {set_number}")

    def update_attached_strands_color(self, parent_strand, color):
        for attached_strand in parent_strand.attached_strands:
            attached_strand.set_color(color)
            logging.info(f"Updated color for attached strand: {attached_strand.layer_name}")
            self.update_attached_strands_color(attached_strand, color)

    def update_set_numbers_after_main_strand_deletion(self, deleted_set_number):
        logging.info(f"Updating set numbers after deleting main strand of set {deleted_set_number}")
        for strand in self.strands:
            if strand.set_number > deleted_set_number:
                strand.set_number -= 1
                strand.layer_name = f"{strand.set_number}_{strand.layer_name.split('_')[1]}"
                logging.info(f"Updated strand {strand.layer_name}'s set number to {strand.set_number}")
        
        self.strand_colors = {k - 1 if k > deleted_set_number else k: v for k, v in self.strand_colors.items()}
        logging.info(f"Updated strand_colors: {self.strand_colors}")
        
        self.update_layer_names()

    def update_layer_names_for_set(self, set_number):
        logging.info(f"Updating layer names for set {set_number}")
        count = 1
        for strand in self.strands:
            if strand.set_number == set_number:
                new_name = f"{set_number}_{count}"
                if strand.layer_name != new_name:
                    logging.info(f"Updated strand name from {strand.layer_name} to {new_name}")
                    strand.layer_name = new_name
                count += 1
        if self.layer_panel:
            self.layer_panel.update_layer_names(set_number)

    def update_layer_names(self):
        logging.info("Starting update_layer_names")
        set_counts = {}
        for strand in self.strands:
            set_number = strand.set_number
            if set_number not in set_counts:
                set_counts[set_number] = 0
            set_counts[set_number] += 1
            new_name = f"{set_number}_{set_counts[set_number]}"
            if new_name != strand.layer_name:
                logging.info(f"Updated layer name from {strand.layer_name} to {new_name}")
                strand.layer_name = new_name
        
        if self.layer_panel:
            logging.info("Updating LayerPanel for all sets")
            self.layer_panel.refresh()
        logging.info("Finished update_layer_names")

    def create_new_set(self):
        new_set_number = max(self.strand_colors.keys(), default=0) + 1
        self.strand_colors[new_set_number] = QColor('purple')
        return new_set_number

    def delete_set(self, set_number):
        if set_number in self.strand_colors:
            del self.strand_colors[set_number]
            self.strands = [s for s in self.strands if s.set_number != set_number]
            self.update_set_numbers_after_main_strand_deletion(set_number)
            self.update()

    def merge_sets(self, set_number1, set_number2):
        if set_number1 in self.strand_colors and set_number2 in self.strand_colors:
            for strand in self.strands:
                if strand.set_number == set_number2:
                    strand.set_number = set_number1
            del self.strand_colors[set_number2]
            self.update_layer_names()
            self.update()

    def split_set(self, set_number, new_set_number):
        if set_number in self.strand_colors:
            new_color = QColor('purple')
            self.strand_colors[new_set_number] = new_color
            for strand in self.strands:
                if strand.set_number == set_number and isinstance(strand, AttachedStrand):
                    strand.set_number = new_set_number
                    strand.set_color(new_color)
            self.update_layer_names()
            self.update()

    def reorder_sets(self, new_order):
        if set(new_order) == set(self.strand_colors.keys()):
            self.strand_colors = {new_order[i]: color for i, color in enumerate(self.strand_colors.values())}
            for strand in self.strands:
                strand.set_number = new_order.index(strand.set_number)
            self.update_layer_names()
            self.update()

    def get_set_strands(self, set_number):
        return [strand for strand in self.strands if strand.set_number == set_number]

    def get_set_color(self, set_number):
        return self.strand_colors.get(set_number, QColor('purple'))

    def set_strand_visibility(self, set_number, visible):
        for strand in self.get_set_strands(set_number):
            strand.visible = visible
        self.update()

    def toggle_set_visibility(self, set_number):
        strands = self.get_set_strands(set_number)
        if strands:
            new_visibility = not strands[0].visible
            self.set_strand_visibility(set_number, new_visibility)

    def get_visible_sets(self):
        return set(strand.set_number for strand in self.strands if strand.visible)

    def update_layer_panel(self):
        if self.layer_panel:
            self.layer_panel.refresh()